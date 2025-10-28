# 🍌 동화 나노바나나 배포 가이드

## 📋 시스템 요구사항

### 필수 요구사항
- **Python**: 3.8 이상
- **메모리**: 최소 2GB RAM
- **저장공간**: 최소 1GB 여유 공간
- **네트워크**: 인터넷 연결 (Gemini API 호출용)

### API 키 요구사항
- **Google Gemini API Key** (필수)
  - Google AI Studio에서 발급
  - 텍스트 생성 및 이미지 생성 권한 필요

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/summit1123/edutech-hackatone.git
cd edutech-hackatone
```

### 2. 가상환경 설정
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정
`.env` 파일을 생성하고 다음 내용 추가:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

### 5. 테스트 실행
```bash
python test_app.py
```

### 6. 애플리케이션 실행
```bash
chainlit run app.py
```

## 🔧 설정 옵션

### 성능 최적화
- 이미지 생성 빈도 조정 (`should_generate_image` 함수)
- 스토리 컨텍스트 크기 제한 (현재 10개)
- 입력 시도 횟수 제한 (현재 3회)

### 보안 설정
- API 키는 반드시 환경변수로 관리
- `.env` 파일은 `.gitignore`에 포함됨
- 사용자 입력 검증 및 필터링 적용

## 📊 모니터링

### 로그 확인
- 콘솔 출력으로 오류 메시지 확인
- API 호출 실패 시 graceful fallback 작동

### 성능 메트릭
- 챕터당 평균 응답 시간
- 이미지 생성 성공률
- 사용자 세션 지속 시간

## 🛠️ 문제 해결

### 일반적인 문제
1. **API 키 오류**
   - `.env` 파일 위치 확인
   - API 키 유효성 검증
   - Gemini API 할당량 확인

2. **이미지 생성 실패**
   - 네트워크 연결 상태 확인
   - API 요청 한도 확인
   - 텍스트는 정상 생성되므로 서비스 지속 가능

3. **메모리 부족**
   - 스토리 컨텍스트 크기 줄이기
   - 이미지 생성 빈도 조정

### 로그 분석
```bash
# 실시간 로그 확인
chainlit run app.py --debug

# 오류 패턴 분석
grep "오류" logs/*.log
```

## 🔄 업데이트

### 코드 업데이트
```bash
git pull origin main
pip install -r requirements.txt --upgrade
python test_app.py
```

### 데이터베이스 마이그레이션
현재 버전은 파일 기반 저장소 사용 (향후 DB 연동 가능)

## 📈 확장성

### 수평 확장
- 여러 인스턴스 실행 가능
- 로드 밸런서 앞단 배치

### 기능 확장
- 새로운 학습 주제 추가
- 언어 지원 확장
- 음성 인터페이스 연동

## 🔐 보안 고려사항

### 데이터 보호
- 사용자 입력 검증 및 새니타이제이션
- API 키 암호화 저장
- 세션 기반 데이터 관리

### 접근 제어
- 현재는 공개 접근
- 필요 시 인증 시스템 추가 가능

## 📞 지원

### 이슈 리포팅
- GitHub Issues 활용
- 오류 로그 및 재현 단계 포함

### 기여 방법
- Fork & Pull Request
- 코딩 스타일 가이드 준수
- 테스트 케이스 포함