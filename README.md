# 딥 러닝을 이용한 명함 인식 시스템
*석정한, *윤준서, **박창우, ***김동호

*동국대학교 컴퓨터공학과, **동국대학교 경영정보학과, ***동국대학교 융합소프트웨어교육원

# A system for business card recognition with deep learning
*Jeonghan Seok, *Junseo Yun, **Changwoo Park, ***Dongho Kim

Dongguk University

*Department of Computer Science and Engineering, **Department of Management Infomation System, ***Convergence Software Institute

e-mail : rudebono@gmail.com, yun6686@gmail.com, ckddn3310@naver.com, dongho.kim@dgu.edu

## 2018 대한전자공학회 하계종합학술대회
### 컴퓨터 소사이어티 부문 (포스터)
CFP-069 p.1160 ~ p.1163

# 프로젝트 소개
동국대학교 컴퓨터공학화 컴퓨터종합설계프로젝트1, 2(교수 김동호)에서 (주)유니포인트 송훈섭 이사, 빅데이터 박사 이현봉 멘토님과 함께 2017년 2학기 ~ 2018년 1학기 동안 수행한 프로젝트임. 본 논문에서는 직접 인공신경망을 구현해서 실험하였고, 본 저장소에 있는 코드는 사용자가 쉽게 사용할 수 있도록 서비스화된 API들로 구현한 결과물임. 명함 인식시스템의 전반부에 해당하는 이미지 처리 부분은 Google Vision을 사용하였고, 후반부에 해당하는 개체명인식 부분은 ETRI API를 사용하였음. Python 3+, Django 프레임워크를 이용하여 웹서비스를 통해 명함 이미지를 받으면 이를 분석하고 명함 정보를 Vcard 포맷으로 생성하여 해당 파일을 사용자가 다운로드 받을 수 있도록 URL를 제공하는 형식임. 카카오톡 플러스친구에 맞게 웹 프레임워크를 작성한 형태임. 카카오톡 플러스친구에게 이미지를 전송하면 해당 이미지 링크를 다운받아 Google Vision에 요청하여 문자를 탐지 및 인식하여 추출하고, 추출된 문자를 ETRI API에 요청하여 개체명인식 결과를 받아 Vcard로 만들어 해당 링크를 반환하는 형태임.
