# 웹사이트 키워드 모니터링 및 텔레그램 알림 프로그램 (V2)

이 프로그램은 특정 웹사이트들의 URL을 주기적으로 감시하여, 설정한 키워드(단일 또는 조합)가 포함된 새로운 게시물이 올라오면 텔레그램으로 즉시 알림을 보내줍니다.

## 🚀 주요 기능

- **실시간 설정 반영**: 프로그램을 끄지 않고 `.env` 파일만 수정해도 다음 주기부터 즉시 적용됩니다.
- **다중 URL 모니터링**: 여러 개의 사이트를 동시에 감시할 수 있습니다.
- **Selenium 동적 렌더링**: 자바스크립트로 로딩되는 사이트(GSP KOCCA 등)도 완벽하게 지원합니다.
- **지능형 키워드 필터링**:
    - **OR 조건**: 쉼표(`,`)로 구분하여 여러 키워드 중 하나만 걸려도 알림.
    - **AND 조건**: `+` 기호를 사용하여 여러 단어가 모두 포함되어야 알림 (예: `AI+수행기관`).
- **사이트별 맞춤형 링크 보정**:
    - **KOCCA PIMS**: "비정상적인 접근" 오류 방지 로직 적용.
    - **GSP KOCCA**: 자바스크립트(`goView`) 내의 ID를 추출하여 직접 상세 페이지로 연결.
- **중복 알림 방지**: `processed_urls.json`을 통해 이미 알림을 보낸 게시물은 다시 보내지 않습니다.

## 🛠 설치 및 설정

### 1. 의존성 설치
```bash
# uv를 사용하는 경우
uv sync

# pip를 사용하는 경우
pip install requests beautifulsoup4 python-dotenv selenium webdriver-manager
```

### 2. 크롬 브라우저 설치 (WSL 환경 필수)
WSL을 사용 중이라면 터미널에서 다음 명령어로 리눅스용 크롬을 설치해야 합니다.
```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb
```

### 3. 환경 변수 설정 (`.env`)
`.env.example`을 참고하여 `.env` 파일을 생성합니다.

```env
TELEGRAM_BOT_TOKEN=123456789:ABCDefGh...
TELEGRAM_CHAT_ID=987654321

# 감시할 URL (쉼표로 구분하여 여러 개 입력 가능)
TARGET_URLS=https://www.nipa.kr/main/main.do,https://www.kocca.kr/kocca/pims/list.do,https://gsp.kocca.kr/web/board/boardContentsListPage.do?board_id=1

# 키워드 설정 (쉼표: OR, 플러스: AND)
KEYWORDS=공고, 지원+사업, AI+수행기관, 메타버스

# 확인 주기 (초 단위)
CHECK_INTERVAL_SECONDS=60
```

## 📖 사용 방법

### 실행
```bash
python main.py
```

### 데이터 리셋 (초기화)
기존에 올라온 게시물을 다시 처음부터 긁어오고 싶을 때 사용합니다.
```bash
rm processed_urls.json
```

## ⚠️ 주의 사항
- **WSL 환경**: 공유 메모리(`shm`) 부족이나 GPU 문제 방지를 위해 코드가 최적화되어 있으나, 크롬 브라우저 자체가 리눅스 내부에 설치되어 있어야 합니다.
- **사이트 차단**: 너무 짧은 확인 주기(예: 10초 이하)는 사이트로부터 IP가 차단될 수 있으므로 주의하세요.
