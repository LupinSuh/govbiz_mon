# 웹사이트 키워드 모니터링 및 알림 프로그램 (V3)

이 프로그램은 특정 공공기관 및 스타트업 지원 사업 공고 페이지를 실시간으로 모니터링하여, 설정한 키워드가 포함된 새로운 게시물이 올라오면 **텔레그램** 및 **구글 챗(Google Chat)**으로 알림을 보내줍니다.

## 🚀 주요 기능

- **실시간 설정 반영**: 프로그램 실행 중에도 `.env` 파일만 수정하면 다음 주기부터 즉시 반영됩니다.
- **다중 채널 알림**: 텔레그램(Telegram)과 구글 챗(Webhook)을 동시에 지원합니다.
- **Selenium & Requests 혼합 엔진**: 
    - 일반 페이지는 **Requests**로 빠르게 처리.
    - 자바스크립트 렌더링이 필요한 CSR(Client Side Rendering) 페이지는 **Selenium**으로 자동 처리.
- **URL 단축 서비스**: 긴 공고 링크와 출처 URL을 **TinyURL(pyshorteners)**을 통해 짧게 변환하여 가독성 높은 알림을 제공합니다.
- **지능형 키워드 필터링**:
    - **OR 조건**: 쉼표(`,`)로 구분하여 여러 키워드 중 하나라도 포함되면 알림.
    - **AND 조건**: `+` 기호를 사용하여 여러 단어가 모두 포함되어야 알림 (예: `AI+수행기관`).
- **제외 키워드 지원**: 알림을 받고 싶지 않은 특정 단어를 포함한 게시물은 제외할 수 있습니다.
- **특화 사이트 지원**:
    - **기업마당(Bizinfo)**: 상세 공고 링크 및 제목 정밀 추출.
    - **스타트업플러스(Startup Plus)**: 하단 게시판 영역(`bl_board_unit`) 데이터 추출 최적화.
    - **KOCCA PIMS & GSP**: 복잡한 자바스크립트 기반 링크 및 접근 권한 문제 해결 로직 적용.

## 🛠 설치 및 설정

### 1. 의존성 설치
```bash
# uv를 사용하는 경우 (권장)
uv sync

# pip를 사용하는 경우
pip install requests beautifulsoup4 python-dotenv selenium webdriver-manager pyshorteners
```

### 2. 크롬 브라우저 설치 (Linux/WSL 환경 필수)
Selenium 작동을 위해 서버/WSL 환경에 크롬 브라우저가 설치되어 있어야 합니다.
```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb
```

### 3. 환경 변수 설정 (`.env`)
`.env` 파일에 다음과 같이 설정을 입력합니다.

```env
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_id
GOOGLE_CHAT_WEBHOOK_URL=your_webhook_url

# 감시할 URL (쉼표로 구분)
TARGET_URLS=https://www.bizinfo.go.kr/sii/siia/selectSIIA200View.do?...,https://www.startup-plus.kr/project,https://www.nipa.kr/home/2-2?curPage=1

# 키워드 설정 (쉼표: OR, 플러스: AND)
KEYWORDS=AI+수행기관, 지원사업, 바우처, 공고

# 제외 키워드
EXCLUDE_KEYWORDS=결과발표, 종료, 마감

# 확인 주기 (초 단위)
CHECK_INTERVAL_SECONDS=60
```

## 📖 사용 방법

### 프로그램 실행
```bash
python main.py
```

### 기록 초기화
기존 게시물 알림을 다시 받고 싶다면 DB 파일을 삭제하세요.
```bash
rm processed_urls.json
```

## ⚠️ 주의 사항
- **확인 주기**: 너무 짧은 주기는 사이트로부터 IP 차단(Blocking)을 유발할 수 있으므로 최소 60초 이상을 권장합니다.
- **Chrome/Driver**: 브라우저 버전과 ChromeDriver 버전이 일치하지 않을 경우 실행 오류가 발생할 수 있습니다.
