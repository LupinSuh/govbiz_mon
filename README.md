# 웹사이트 키워드 모니터링 및 알림 프로그램 (V4)

이 프로그램은 정부 지원 사업, 공공기관 공고 및 스타트업 프로젝트 페이지를 실시간으로 모니터링하여, 설정한 키워드가 포함된 새 게시물을 다중 소셜 서비스(텔레그램, 구글 챗, 디스코드, 슬랙)로 즉시 전송합니다.

## 🚀 주요 기능

- **OS 무관 (OS-Agnostic)**: Windows, Linux(WSL), macOS 어디서든 별도의 크롬 드라이버 설치 없이 즉시 실행 가능 (`webdriver-manager` 적용).
- **다중 채널 알림**: 텔레그램, 구글 챗, **디스코드**, **슬랙** 웹훅을 통한 동시 알림 지원.
- **직결 하이퍼링크**: 중간 단축 사이트를 거치지 않고, 제목 클릭 시 원본 공고 페이지로 **직접 연결**되는 깔끔한 메시지 UI.
- **지능형 엔진**: 
    - 일반 페이지: 가벼운 **Requests** 엔진으로 고속 처리.
    - 동적 페이지: 자바스크립트 렌더링이 필요한 CSR 사이트는 **Selenium**으로 자동 처리.
- **정밀 필터링**:
    - **OR 조건**: 쉼표(`,`)로 구분된 단어 중 하나라도 포함 시 알림.
    - **AND 조건**: `+` 기호를 사용하여 여러 단어가 모두 포함되어야 알림 (예: `AI+바우처`).
- **제외 키워드**: 알림에서 제외하고 싶은 단어(예: 마감, 종료) 설정 가능.
- **특화 사이트 최적화**: 기업마당(Bizinfo), KOCCA PIMS/GSP, 스타트업플러스 등 주요 공고 사이트 맞춤형 데이터 추출 로직 탑재.

## 🛠 설치 및 설정

### 1. 의존성 설치 (`uv` 권장)
```bash
# uv를 사용하는 경우
uv sync

# 일반 pip 사용 시
pip install beautifulsoup4 python-dotenv requests schedule selenium webdriver-manager
```

### 2. 환경 변수 설정 (`.env`)
`.env.example` 파일을 참고하여 `.env` 파일을 생성하고 필요한 토큰/웹훅 URL을 입력하세요.

```env
# 알림 설정 (필요한 서비스만 입력)
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
GOOGLE_CHAT_WEBHOOK_URL=...
DISCORD_WEBHOOK_URL=...
SLACK_WEBHOOK_URL=...

# 감시 설정
TARGET_URLS=URL1, URL2...
KEYWORDS=AI+수행기관, 지원사업
EXCLUDE_KEYWORDS=마감, 종료
CHECK_INTERVAL_SECONDS=60
```

## 📖 실행 방법

```bash
# uv를 통한 실행 (추천)
uv run python main.py

# 일반 실행
python main.py
```

## ⚠️ 주의 사항
- **Chrome 설치 필수**: 본체에 구글 크롬 브라우저가 설치되어 있어야 합니다 (드라이버는 프로그램이 자동 관리합니다).
- **차단 방지**: 너무 짧은 확인 주기(예: 10초 미만)는 사이트로부터 IP 차단을 유발할 수 있으므로 60초 이상을 권장합니다.
- **파일 권한**: 프로그램이 `processed_urls.json` 파일에 쓰기 권한을 가지고 있어야 합니다.
