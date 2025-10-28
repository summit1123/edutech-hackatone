# 🍌 동화 나노바나나 📚

> 경계선 지능 아동을 위한 AI 기반 맞춤형 동화책 생성 플랫폼

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Chainlit](https://img.shields.io/badge/Chainlit-1.1+-green.svg)](https://chainlit.io/)
[![Google Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-orange.svg)](https://ai.google.dev/)

## ✨ 주요 기능

### 🎯 **개인 맞춤형 동화 생성**
- 3단계 사용자 정보 수집 (학습 주제, 성향, 선호도)
- 경계선 지능 아동 특화 언어 및 구조
- 실시간 상호작용 기반 스토리 전개

### 🎨 **AI 이미지 생성**
- Google Gemini 2.5 Flash Image 활용
- 캐릭터 일관성 유지 시스템
- 성능 최적화된 선택적 이미지 생성

### 📚 **학습 요소 통합**
- 자연스러운 교육 콘텐츠 포함
- 사용자 의도 분석 및 맞춤 피드백
- 진행도 추적 및 시각화

### 🛡️ **안전성 & 사용성**
- 강력한 에러 핸들링 시스템
- 사용자 친화적 복구 메커니즘
- 종합적인 도움말 및 가이드

## 🚀 빠른 시작

### 1. 설치
```bash
git clone https://github.com/summit1123/edutech-hackatone.git
cd edutech-hackatone
pip install -r requirements.txt
```

### 2. 환경 설정
```bash
# .env 파일 생성
echo "GEMINI_API_KEY=your_gemini_api_key" > .env
```

### 3. 실행
```bash
# 테스트 실행
python test_app.py

# 애플리케이션 시작
chainlit run app.py
```

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   사용자 입력    │ -> │  StoryTeller     │ -> │  Gemini AI      │
│   (3단계 폼)     │    │  (상태 관리)      │    │  (텍스트+이미지) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         v                       v                       v
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   입력 검증      │    │  컨텍스트 관리    │    │  응답 생성       │
│   & 에러 처리    │    │  & 맥락 유지      │    │  & 이미지 생성   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📊 기술 스택

| 카테고리 | 기술 |
|----------|------|
| **Frontend** | Chainlit (Python Web UI) |
| **AI Model** | Google Gemini 2.5 Flash |
| **Image Gen** | Google Gemini 2.5 Flash Image |
| **Language** | Python 3.8+ |
| **Deployment** | Local/Cloud Ready |

## 🎮 사용 방법

### 1단계: 학습 주제 선택
```
💡 예시: "숫자", "색깔", "동물", "한글"
```

### 2단계: 사용자 소개
```
💡 예시: "6살이고 호기심이 많아요"
```

### 3단계: 선호도 입력
```
💡 예시: "강아지와 파란색을 좋아해요"
```

### 동화 진행
- **"동화 시작"** 입력으로 이야기 시작
- 자유로운 대화로 스토리 전개
- 챕터별 진행도 확인

## 🔧 설정 옵션

### 성능 튜닝
```python
# 이미지 생성 빈도 조정
def should_generate_image(self, chapter_num):
    return chapter_num == 1 or chapter_num % 3 == 0

# 컨텍스트 크기 제한
MAX_CONTEXT_SIZE = 10
```

### 안전 설정
```python
# 입력 검증 강화
MAX_INPUT_LENGTH = 100
MAX_ATTEMPTS = 3
```

## 🧪 테스트

```bash
# 전체 테스트 실행
python test_app.py

# 개별 컴포넌트 테스트
python -c "import app; print('✅ Import Success')"
```

## 📈 성능 메트릭

- **응답 시간**: 평균 3-5초 (텍스트), 10-15초 (이미지)
- **메모리 사용량**: 평균 200MB
- **API 호출 최적화**: 선택적 이미지 생성으로 비용 절약

## 🤝 기여하기

1. Fork 프로젝트
2. Feature 브랜치 생성 (`git checkout -b feature/AmazingFeature`)
3. 변경사항 커밋 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 Push (`git push origin feature/AmazingFeature`)
5. Pull Request 생성

## 📝 라이센스

이 프로젝트는 MIT 라이센스를 따릅니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 🔗 관련 링크

- [배포 가이드](DEPLOYMENT_GUIDE.md)
- [API 문서](https://ai.google.dev/docs)
- [Chainlit 문서](https://docs.chainlit.io/)

## 📞 지원

- **Issues**: [GitHub Issues](https://github.com/summit1123/edutech-hackatone/issues)
- **Discussions**: [GitHub Discussions](https://github.com/summit1123/edutech-hackatone/discussions)

---

<div align="center">

**🍌 Made with ❤️ for children's education 📚**

[⭐ Star this repo](https://github.com/summit1123/edutech-hackatone) if you find it helpful!

</div>