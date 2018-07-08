from django.http import HttpResponse
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import re
import json
import requests
import base64
import random
import time
import hashlib


################
# http 요청함수#
################
def vcard(_request, _filename):

    _filepath = 'data/vcard/'+_filename

    with open(_filepath, 'rb') as _f :
        _response = HttpResponse(_f, content_type='text/x-vcard')
        # 필요한 응답헤더 세팅
        _response['Content-Disposition'] = 'attachment; filename="{}"'.format(_filename)
        return _response



####################
# 카카오 요청 함수 #
####################
# keyboard/
def keyboard(_request):

    # 카카오톡 키보드 모드를 사용하지 않는 셋팅.
    # 단순히 사용자에게 문자나 사진만 받는다.
    _response = JsonResponse({
        "type" : "text"
    })

    return _response


# message
@csrf_exempt # message 로 들어오기 때문에 csrf 해제해줘야한다.
def message(_request):

    _requestBody = ( (_request.body).decode("utf-8") )
    _jsonData = json.loads(_requestBody)

    _msgType = _jsonData["type"]
    _msgContent = _jsonData["content"]

    _response = JsonResponse({})
    # 사용자가 명함 사진을 전송했을 경우.
    if _msgType == "photo" :
        _response = message_type_photo(_msgContent) # _msgContent는 이미지 URL

    # 그외 전송했을 경우.
    else :
        _response = message_type_other()

    return _response


#########################
# 프로그램 내 사용 함수 #
#########################
def message_type_other() :
    
    _answer = ''

    _f = open("data/introduction.txt", 'r', encoding='utf8')
    _lines = _f.readlines() # 배열로 가져온다.
    _f.close()

    # 문자열로 변환한다.
    for _line in _lines:
        _answer += _line

    _response = JsonResponse({"message" : {"text" : _answer}})
    
    return _response


# 사용자가 이미지를 전송했을때 이 함수를 통해 처리한다.
# 이미지 URL를 입력받고 JSON 답을 출려한다.
def message_type_photo(_imgURL) :

    _answer = ''

    #######################################
    # 1. 카카오톡 서버에서 이미지 다운받기#
    #######################################
    try :
        _1_imgData = requests.get(_imgURL).content
    except :
        _error = 'ERROR : 카카오톡 서버에서 이미지를 다운 받을 수 없습니다.'
        _error_response = JsonResponse({"message" : {"text" : _error}})
        return _error_response

    try :
        _1_imgBase64 = base64.b64encode(_1_imgData).decode("utf-8")
    except :
        _error = 'ERROR : 이미지를 base65로 encoding 할 수 없습니다.'
        _error_response = JsonResponse({"message" : {"text" : _error}})
        return _error_response


    ###########################################
    # 2. 구글 클라우드 비전으로 문자 추출하기 #
    ###########################################
    _2_GOOGLE_API_KEY = ""
    _2_GOOGLE_API_URL = "https://vision.googleapis.com/v1/images:annotate?key=" + _2_GOOGLE_API_KEY
    _2_GOOGLE_API_DATA = {
        "requests": [{
        "image": {"content": _1_imgBase64},
        "features": [{"type": "TEXT_DETECTION"}]
        }]
    }

    # 구글 클라우드 비전에 요청을 보내어 결과 받아오기.
    try :
        _2_resString = requests.post(_2_GOOGLE_API_URL, json=_2_GOOGLE_API_DATA)
    except :
        _error = 'ERROR : 구글 클라우드 비전과 통신이 불가능합니다.'
        _error_response = JsonResponse({"message" : {"text" : _error}})
        return _error_response

    try :
        _2_resJson = _2_resString.json() # 결과 string을 json으로 변환
    except :
        _error = 'ERROR : 구글 클라우드 비전로 받은 결과를 json으로 변환할 수 없습니다.'
        _error_response = JsonResponse({"message" : {"text" : _error}})
        return _error_response

    # 탐지 및 인식 된 문자 가져오기.
    try :
        _2_bcString = _2_resJson["responses"][0]["textAnnotations"][0]["description"] # 탐지된 문자가져오기
        _2_bcString = _2_bcString.replace('\n', '  ')
    except :
        _error = 'ERROR : 이미지 속 문자를 탐지 및 인식하지 못했습니다.'
        _error_response = JsonResponse({"message" : {"text" : _error}})
        return _error_response

    
    ###############################
    # 3. ETRI으로 개체명 분석하기 #
    ###############################
    _3_ETRI_API_KEY   = ""
    _3_ETRI_API_URL   = "http://aiopen.etri.re.kr:8000/WiseNLU"
    _3_ETRI_API_DATA  = {
        "request_id": "reserved field",
        "access_key": _3_ETRI_API_KEY,
        "argument": {
            "text": _2_bcString,
            "analysis_code": "srl"
        }
    }

    # ETRI 서버에 개체명인식 request 보내기
    try :
        _3_resString = requests.post(_3_ETRI_API_URL, json=_3_ETRI_API_DATA)
    except :
        _error = 'ERROR : 개체명 인식 서버와 통신할 수 없습니다.'
        _error_response = JsonResponse({"message" : {"text" : _error}})
        return _error_response

    # 결과값을 json으로 변환하기
    try :
        _3_resJson = _3_resString.json()
    except :
        _error = 'ERROR : 개체명 인식 결과를 json으로 변환할 수 없습니다.'
        _error_response = JsonResponse({"message" : {"text" : _error}})
        return _error_response

    # json에서 sentence 가져오기
    try :
        _3_sentence_list = _3_resJson["return_object"]["sentence"]
    except :
        _error = 'ERROR : 현재 개체명 인식 서버에 너무 많은 요청이 들어왔습니다. 나중에 다시 시도해주세요.'
        _error = _2_bcString
        _error_response = JsonResponse({"message" : {"text" : _error}})
        return _error_response

   # sentence에서 개체명 인식 찾기
    try : 
        _3_ne_list_list = []
        for _3_sentence in _3_sentence_list :
            _3_ne_list_list.append(_3_sentence["NE"])
        if not _3_ne_list_list:
            _error = 'ERROR : 개체명 인식을 할 수 없습니다.'
            _error_response = JsonResponse({"message" : {"text" : _error}})
            return _error_response
    except:
        _error = 'ERROR : sentence 영역에서 NE 영역을 찾을 수 없습니다.'
        _error_response = JsonResponse({"message" : {"text" : _error}})
        return _error_response

   
    # 개체명이 담길 변수
    _3_NAME = ''
    _3_ADDR = ''
    _3_URL = ''
    _3_NUMBER = ''
    _3_ORGANIZATION = ''


    # 개체명 이중배열을 파싱하여 개체명을 찾는다.
    for _3_ne_list in _3_ne_list_list :
        for _3_ne in _3_ne_list:

            # 이름
            if _3_ne["type"] == "PS_NAME":
                _3_NAME += _3_ne["text"]

            # 주소
            if _3_ne["type"].find("LC_") > -1 or\
               _3_ne["type"].find("LCP_") > -1 or\
               _3_ne["type"].find("AF_") > -1 or\
               _3_ne["type"] == "QT_ORDER" or\
               _3_ne["type"] == "QT_ZIPCODE" or\
               _3_ne["type"] == "QT_OTHERS" or\
               _3_ne["type"] == "TM_DIRECTION" or\
               _3_ne["type"] == "QT_SPORTS" :
                   _3_ADDR += _3_ne["text"]
                   _3_ADDR += ' '

            # URL
            if _3_ne["type"] == "TMI_EMAIL" or\
               _3_ne["type"] == "TMI_SITE" :
                _3_URL += _3_ne["text"]
                _3_URL += ' '

            # 번호
            if _3_ne["type"] == "QT_PHONE" :
                _3_temp = re.sub('[^0-9]', '', _3_ne["text"])
                if len(_3_temp) > 8:
                    _3_NUMBER += _3_temp
                    _3_NUMBER += ' '

            # 조직명
            if _3_ne["type"].find("OG_") > -1 or\
               _3_ne["type"].find("OGG_") > -1 or\
               _3_ne["type"].find("CV_") > -1 :
                _3_ORGANIZATION += _3_ne["text"]
                _3_ORGANIZATION += ' '

    # 문자열 처리
    _3_bcr_org = ''
    _3_bcr_name = ''
    _3_bcr_addr = ''
    _3_bcr_email = ''
    _3_bcr_num = ''

    ## 조직명
    _3_bcr_org = _3_ORGANIZATION

    ## 이름
    _3_bcr_name = re.sub(u'[^가-힣]+', '', _3_NAME)
    if _3_bcr_name == '' :
        _3_ORG_list = _3_ORGANIZATION.split()
        for _3_ORG in _3_ORG_list:
            _3_temp = re.sub(u'[^가-힣]+', '', _3_ORG)
            if len(_3_temp) == 3:
                _3_bcr_name = _3_temp
                _3_bcr_org = _3_bcr_org.replace(_3_temp, '')
                _3_bcr_org = re.sub("\s\s\s+", " ", _3_bcr_org)
                _3_bcr_org = re.sub("\s\s+", " ", _3_bcr_org)
                break

    ## 주소
    _3_bcr_addr = re.sub(u'[^가-힣\s|0-9]+', '', _3_ADDR)

    ## 이메일
    try:
        _3_bcr_email = re.search(u'(\w+[\w\.]*)@(\w+[\w\.]*)\.([A-Za-z]+)', _3_URL).group()
    except:
        _3_bcr_email = ''

    # 이메일
    _3_bcr_num = _3_NUMBER


    ###################
    # 4. vCard 만들기 #
    ###################

    # vCard 3.0 포맷인 문자열을 만든다.
    _4_vcf_string = 'BEGIN:VCARD\n' +\
        'VERSION:3.0\n' +\
        'N:' + _3_bcr_name + ';;;;\n' +\
        'ORG:' + _3_bcr_org + ';\n' +\
        'EMAIL;type=INTERNET;type=WORK;type=pref:' + _3_bcr_email + '\n'
    for _3_bcr_n in _3_bcr_num.split():
        _4_vcf_string += 'TEL;type=WORK;type=VOICE;type=pref:' + _3_bcr_n + '\n'
    _4_vcf_string += 'ADR;type=WORK;type=pref:;;' + _3_bcr_addr + '\n'
    _4_vcf_string += 'END:VCARD'

    # 해당 문자열을 파일로 생성한다.
    _4_vcf_filename = hashlib.md5(_4_vcf_string.encode('utf-8')).hexdigest() + '.vcf'
    _4_f = open('data/vcard/'+_4_vcf_filename, 'w')
    _4_f.write(_4_vcf_string)
    _4_f.close()
    

    # `답을 보낸다.
    _answer = '* 명함 인식 결과 *\n\n' +\
        '* 조직명\n' + _3_bcr_org + '\n\n' +\
        '* 이름\n' + _3_bcr_name + '\n\n' +\
        '* 주소\n' + _3_bcr_addr + '\n\n' +\
        '* 이메일\n' + _3_bcr_email + '\n\n' +\
        '* 전화번호\n' + _3_bcr_num + '\n\n'

    _answer += '* vCard 파일\n'
    _answer += 'http://210.89.190.125/vcard/'+_4_vcf_filename

    _answer += '\n\n'
    _answer += '*주의* 아이폰 카카오톡 웹 브라우저는 vCard 파일을 지원하지 않습니다. 링크를 복사하여 다른 웹 브라우저에서 열어주세요.'

    #_answer = 'http://210.89.190.125/vcard/'+_4_vcf_filename

    _response = JsonResponse({"message" : {"text" : _answer}})
    
    return _response
