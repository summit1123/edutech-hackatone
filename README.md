# 동화 나노바나나 🍌📚

경계선 지능 아동을 위한 AI 동화책 생성 애플리케이션

## 기능
- 사용자 맞춤형 동화 스토리 생성
- Gemini 2.5 Flash Image를 활용한 일관성 있는 이미지 생성
- 인터랙티브 스토리텔링
- 학습 요소 포함

## 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정
`.env` 파일을 생성하고 다음을 추가:
```
GEMINI_API_KEY=your_api_key_here
```

### 3. 실행
```bash
chainlit run app.py
```

## 기술 스택
- **Frontend**: Chainlit
- **AI Model**: Google Gemini 2.5 Flash (Text + Image)
- **Language**: Python
- **Image Generation**: google-genai SDK

## 프로젝트 구조
```
├── app.py              # 메인 Chainlit 애플리케이션
├── main.py             # 대안 실행 파일
├── test_models.py      # 모델 테스트 스크립트
├── requirements.txt    # 의존성 목록
└── .env               # 환경변수 (API 키)
```