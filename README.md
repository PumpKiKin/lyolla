# 로욜라 도서관 챗봇 '룔라'

서강대학교 로욜라 도서관 웹페이지와 공지사항 데이터를 기반으로 한 **챗봇 서비스**입니다.\
Django + LangChain + FAISS + Google Generative AI(Gemini)를 활용해 구현했습니다.\
사용자가 웹에서 질문을 입력하면, 벡터DB에서 관련 정보를 검색한 후 AI가 답변을 생성합니다.\
대화 맥락을 유지하기 위해 이전 대화의 내용을 참고합니다.

접속 링크: [http://18.209.6.7/chat/](http://18.209.6.7/chat/)

---

## 기능 소개
- **FAQ 챗봇**: 도서관 이용 안내, 시설 정보, 공지사항 관련 내용 자동 응답
- **RAG (Retrieval-Augmented Generation)**: FAISS 벡터 DB 기반 검색 후 LLM 응답

---

## 기술 스택
- **Backend**: Django, Django REST Framework
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **Vector DB**: FAISS
- **Embedding**: HuggingFace (ko-sbert-nli)
- **LLM**: Google Generative AI (Gemini 2.5 Flash)

---

## 디렉토리 구조
```
lyolla
├── chatbot_app/               # Django 앱 (API + View + Template)
│   ├── static/
│   │   ├── chatbot_app/    # CSS, JS
│   │   │   ├── chat.js
│   │   │   └── style.css
│   │   ├── fonts/
│   │   │   ├── SOGANG_UNIVERSITY_for_mac.otf
│   │   │   └── SOGANG_UNIVERSITY_for_windows.ttf
│   ├── templates/chatbot_app/ # HTML 템플릿
│   │   └── chat.html
│   ├── api.py                 # LLM 연결 및 RAG 처리 로직
│   ├── embeddings.py          # 벡터DB 구축 스크립트
│   ├── views.py               # Django View
│   └── urls.py
├── database/                  # JSON 데이터셋
│   ├── detail_data.json       # 도서관 홈페이지 크롤링 데이터
│   └── notices.json           # 공지사항 크롤링 데이터
├── faiss_index/               # FAISS 인덱스 저장 위치
├── django_project/            # Django 프로젝트 설정
├── manage.py
├── pyproject.toml             # poetry 가상환경
├── .gitignore
└── README.md
````

---

## 설치 및 실행 방법 (개발용)

### 1. 저장소 클론
```bash
git clone https://github.com/PumpKiKin/lyolla.git
cd lyolla
````

### 2. 가상환경 설정

```bash
# Poetry
poetry install
poetry shell
```

### 3. 환경변수 설정

`.env` 파일 생성 후 아래 추가:

```
GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
DJANGO_SECRET_KEY=YOUR_DJANGO_SECRET_KEY
```

### 4. DB 스키마 업데이트(최초 1회만 실행)

```bash
poetry run python manage.py migrate
```

### 5. 서버 실행

```bash
poetry run python manage.py runserver
```

브라우저에서 [http://127.0.0.1:8000/chat/](http://127.0.0.1:8000/chat/) 접속

---

## 프로젝트 정보
* **2025-하계 탐구 공동체 "객체 지향 인공지능 에이전트 개발 방법론"**
  * 서강대학교 교수학습센터 주관

* **프로젝트 개발** : **펌키킨** 팀
  * 서강대학교 국어국문학과 4학년 김현서
    * **이메일**: neulbokim@sogang.ac.kr
  * 서강대학교 국어국문학과 3학년 최윤지
    * **이메일**: yunji3711@naver.com
* **지도 교수**: 서강대학교 메타버스전문대학원 김태훈 전임교수
  * **이메일**: taehoonkim@sogang.ac.kr
  * **홈페이지** : https://mimic-lab.com/

---
