import os
import json
import time
import requests
import re
import pyshorteners
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs

# Selenium 관련 임포트
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 이미 처리된 게시물 URL 저장 파일
DB_FILE = "processed_urls.json"

def shorten_url(url):
    """pyshorteners를 사용하여 긴 URL을 단축합니다. (TinyURL 서비스 사용)"""
    try:
        s = pyshorteners.Shortener()
        return s.tinyurl.short(url)
    except Exception as e:
        # 단축 실패 시 원본 URL 반환
        return url

def get_config():
    load_dotenv(override=True)
    return {
        "BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
        "CHAT_ID": os.getenv("TELEGRAM_CHAT_ID"),
        "GOOGLE_CHAT_WEBHOOK_URL": os.getenv("GOOGLE_CHAT_WEBHOOK_URL"),
        "TARGET_URLS": [url.strip() for url in os.getenv("TARGET_URLS", "").split(",") if url.strip()],
        "KEYWORDS": [k.strip() for k in os.getenv("KEYWORDS", "").split(",") if k.strip()],
        "EXCLUDE_KEYWORDS": [k.strip() for k in os.getenv("EXCLUDE_KEYWORDS", "").split(",") if k.strip()],
        "CHECK_INTERVAL": int(os.getenv("CHECK_INTERVAL_SECONDS", 60))
    }

def load_processed_urls():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_processed_urls(urls):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(list(urls), f, ensure_ascii=False, indent=2)

def send_telegram_message(config, title, url, site_url, matched_keyword):
    if not config["BOT_TOKEN"] or not config["CHAT_ID"]:
        return
    
    # URL 단축 적용
    short_url_val = shorten_url(url)
    short_site_url = shorten_url(site_url)
    
    message = (
        f"🔔 [새 게시물 알림]\n\n"
        f"<b>키워드:</b> #{matched_keyword}\n"
        f"<b>출처:</b> {short_site_url}\n"
        f"<b>제목:</b> {title}\n"
        f"<b>링크:</b> {short_url_val}"
    )
    api_url = f"https://api.telegram.org/bot{config['BOT_TOKEN']}/sendMessage"
    payload = {"chat_id": config["CHAT_ID"], "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(api_url, data=payload, timeout=10)
        if response.status_code == 200:
            print(f"[{datetime.now()}] 텔레그램 알림 전송 성공: {title} (키워드: {matched_keyword})")
        else:
            print(f"[{datetime.now()}] 텔레그램 알림 전송 실패: {response.text}")
    except Exception as e:
        print(f"[{datetime.now()}] 텔레그램 전송 중 오류 발생: {e}")

def send_google_chat_message(config, title, url, site_url, matched_keyword):
    webhook_url = config.get("GOOGLE_CHAT_WEBHOOK_URL")
    if not webhook_url:
        return
    
    # URL 단축 적용
    short_url_val = shorten_url(url)
    short_site_url = shorten_url(site_url)
    
    message = (
        f"🔔 *[새 게시물 알림]*\n\n"
        f"*키워드:* #{matched_keyword}\n"
        f"*출처:* {short_site_url}\n"
        f"*제목:* {title}\n"
        f"*링크:* {short_url_val}"
    )
    
    payload = {"text": message}
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"[{datetime.now()}] 구글챗 알림 전송 성공: {title}")
        else:
            print(f"[{datetime.now()}] 구글챗 알림 전송 실패: {response.text}")
    except Exception as e:
        print(f"[{datetime.now()}] 구글챗 전송 중 오류 발생: {e}")

def send_notifications(config, title, url, site_url, matched_keyword):
    send_telegram_message(config, title, url, site_url, matched_keyword)
    send_google_chat_message(config, title, url, site_url, matched_keyword)

def get_links_via_selenium(target_url):
    """Selenium을 사용하여 렌더링된 페이지의 링크를 추출합니다."""
    print(f"[{datetime.now()}] Selenium으로 렌더링 중... {target_url}")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless") # 화면 없이 실행
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu") # WSL 환경에서 필수인 경우가 많음
    chrome_options.add_argument("--remote-debugging-port=9222") # 포트 충돌 방지
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.binary_location = "/usr/bin/google-chrome"
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = None
    extracted_data = []
    
    try:
        service = Service(executable_path="/home/lupin/chromedriver-linux64/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(target_url)
        
        # 게시판 리스트가 로드될 때까지 대기 (최대 10초)
        wait = WebDriverWait(driver, 10)
        
        # 사이트별 로딩 대기 및 전처리
        if "gsp.kocca.kr" in target_url:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "tbody")))
        elif "bizinfo.go.kr" in target_url:
            # txt_list 대신 게시물 링크를 포함하는 txt_l 클래스 대기
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "txt_l")))
        elif "startup-plus.kr" in target_url:
            # 게시판 형태인 bl_board_unit 요소가 나타날 때까지 대기
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "bl_board_unit")))
            time.sleep(2)

        # 페이지 소스를 가져와서 BeautifulSoup으로 파싱
        soup = BeautifulSoup(driver.page_source, "html.parser")


        # 스타트업플러스 게시판 특화 처리
        if "startup-plus.kr" in target_url:
            board_units = soup.find_all(class_="bl_board_unit")
            for unit in board_units:
                link_tag = unit.find("a", href=True)
                if link_tag and "/project/" in link_tag["href"]:
                    href = urljoin(target_url, link_tag["href"])
                    # 제목은 bl_board_subject 또는 a 태그 내부 텍스트
                    title_tag = unit.find(class_="bl_board_subject")
                    title = title_tag.get_text(strip=True) if title_tag else link_tag.get_text(strip=True)
                    if title:
                        extracted_data.append({"title": title, "href": href})
            return extracted_data # 스타트업플러스는 여기서 종료

        links = soup.find_all("a", href=True)

        for link in links:
            title = link.get_text(strip=True)
            href = link["href"]
            onclick = link.get("onclick", "")

            # GSP 사이트 특수 처리 (javascript:goView, contentsView 등)
            if "gsp.kocca.kr" in target_url:

                combined = str(href) + str(onclick)
                
                # 1. goView('1', '345') 형태 처리
                if "goView" in combined:
                    ids = re.findall(r"goView\s*\(\s*['\"]([a-zA-Z0-9]+)['\"]", combined)
                    # 두 번째 ID(contents_id)까지 필요한 경우를 위해 보강
                    all_ids = re.findall(r"['\"]([a-zA-Z0-9]+)['\"]", combined)
                    if len(all_ids) >= 2:
                        href = f"https://gsp.kocca.kr/web/board/boardContentsViewPage.do?board_id={all_ids[0]}&board_contents_id={all_ids[1]}"
                
                # 2. contentsView('ea84e01b...') 형태 처리 (현재 이 사이트에서 사용 중)
                elif "contentsView" in combined:
                    match = re.search(r"contentsView\s*\(\s*['\"]([a-zA-Z0-9]+)['\"]", combined)
                    if match:
                        content_id = match.group(1)
                        # board_id는 URL 파라미터에서 추출하거나 기본값 1 사용
                        parsed_target = urlparse(target_url)
                        target_qs = parse_qs(parsed_target.query)
                        b_id = target_qs.get("board_id", ["1"])[0]
                        href = f"https://gsp.kocca.kr/web/board/boardContentsViewPage.do?board_id={b_id}&board_contents_id={content_id}"
                
                # 3. 이미 URL 파라미터가 있는 경우 (board_id, board_contents_id 또는 contents_id)
                elif "boardContentsViewPage.do" not in href and ("board_contents_id=" in combined or "contents_id=" in combined):
                    parsed = urlparse(href if href.startswith("http") else urljoin(target_url, href))
                    qs = parse_qs(parsed.query)
                    b_id = qs.get("board_id", ["1"])[0]
                    c_id = qs.get("board_contents_id") or qs.get("contents_id")
                    if c_id:
                        href = f"https://gsp.kocca.kr/web/board/boardContentsViewPage.do?board_id={b_id}&board_contents_id={c_id[0]}"

            # Bizinfo 사이트 특수 처리
            elif "bizinfo.go.kr" in target_url:
                if "selectSIIA200Detail.do" in href:
                    if not title: # 제목이 없는 경우 부모 요소나 이미지 alt 확인
                        title = link.get("title", "").strip()
                    if not title:
                        parent_text = link.parent.get_text(strip=True)
                        if parent_text:
                            title = parent_text

            # StartupPlus 사이트 특수 처리
            elif "startup-plus.kr" in target_url:
                if "/project/" in href and "apply" not in href:
                    if not title or title in ["Shortcuts", "Shortcut", "Apply"]:
                        # 카드 형태에서 제목 추출 시도
                        parent = link.find_parent()
                        if parent:
                            # Accelerating2026년... 형태에서 카테고리명 등을 제외하려 노력
                            title = parent.get_text(strip=True).replace("Shortcuts", "").replace("Shortcut", "").replace("Apply", "")
                            # 너무 길면 자르거나 특정 키워드(공고) 주변만 추출할 수도 있음
            
            if not href.startswith("http") and not href.startswith("javascript"):
                href = urljoin(target_url, href)
            
            if title and len(title) > 2: # 너무 짧은 제목 제외
                extracted_data.append({"title": title, "href": href})
                
    except Exception as e:
        print(f"[{datetime.now()}] Selenium 오류: {e}")
    finally:
        if driver:
            driver.quit()
            
    return extracted_data

def monitor_sites(config, processed_urls):
    new_found = False
    
    for target_url in config["TARGET_URLS"]:
        print(f"[{datetime.now()}] 모니터링 시작: {target_url}")
        
        try:
            # 특정 도메인은 Selenium 사용, 그 외는 requests 사용
            # kocca.kr (PIMS)는 requests가 더 잘 작동하므로 gsp.kocca.kr만 Selenium 사용 유지
            if any(domain in target_url for domain in ["gsp.kocca.kr", "bizinfo.go.kr", "startup-plus.kr"]):
                posts = get_links_via_selenium(target_url)
            else:
                # 일반 사이트는 requests로 빠르게 처리
                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(target_url, headers=headers, timeout=15)
                soup = BeautifulSoup(response.text, "html.parser")
                
                posts = []
                for a in soup.find_all("a", href=True):
                    title = a.get_text(strip=True)
                    # 제목이 없는 경우 title 속성이나 부모 요소 텍스트 확인 (NIPA 등 대응)
                    if not title:
                        title = a.get("title", "").strip()
                    if not title:
                        # <td> 안에 <a>가 있는 경우 <td>의 다른 텍스트 확인
                        title = a.parent.get_text(strip=True)
                        
                    if title and len(title) > 2:
                        posts.append({"title": title, "href": urljoin(target_url, a["href"])})

            for post in posts:
                title = post["title"]
                href = post["href"]
                
                # KOCCA PIMS (www.kocca.kr) 보정
                if "kocca.kr/kocca/pims" in href and "menuNo=204135" not in href:
                    if "menuNo=" in href:
                        href = href.replace("menuNo=", "menuNo=204135")
                    else:
                        href += "&menuNo=204135"

                if href not in processed_urls:
                    # 1. 제외 키워드 먼저 확인
                    is_excluded = False
                    for ex_kw in config["EXCLUDE_KEYWORDS"]:
                        if ex_kw in title:
                            is_excluded = True
                            break
                    
                    if is_excluded:
                        processed_urls.add(href) # 중복 알림 방지를 위해 처리 완료로 간주
                        continue

                    # 2. 매칭된 키워드 찾기 (AND 조건 지원: AI+수행기관)
                    matched_keyword = None
                    for kw_entry in config["KEYWORDS"]:
                        if "+" in kw_entry:
                            # '+'로 연결된 모든 단어가 포함되어 있는지 확인 (AND 조건)
                            sub_keywords = [sk.strip() for sk in kw_entry.split("+") if sk.strip()]
                            if all(sk in title for sk in sub_keywords):
                                matched_keyword = kw_entry
                                break
                        else:
                            # 단일 키워드 포함 확인
                            if kw_entry in title:
                                matched_keyword = kw_entry
                                break

                    if matched_keyword:
                        send_notifications(config, title, href, target_url, matched_keyword)
                        processed_urls.add(href)
                        new_found = True

            
        except Exception as e:
            print(f"[{datetime.now()}] {target_url} 모니터링 오류: {e}")

    return new_found

def main():
    print("="*50)
    print("웹사이트 모니터링 프로그램 (Selenium 지원 버전)")
    print("="*50)
    processed_urls = load_processed_urls()
    while True:
        try:
            config = get_config()
            has_telegram = config.get("BOT_TOKEN") and config.get("CHAT_ID")
            has_google_chat = config.get("GOOGLE_CHAT_WEBHOOK_URL")
            
            if not (has_telegram or has_google_chat) or not config["TARGET_URLS"]:
                print(f"[{datetime.now()}] 설정 오류: .env 파일을 확인하세요 (텔레그램 또는 구글챗 설정 필수).")
                time.sleep(10)
                continue
            if monitor_sites(config, processed_urls):
                save_processed_urls(processed_urls)
            # 다음 주기까지 대기 (카운트다운을 한 줄에서 업데이트)
            interval = config["CHECK_INTERVAL"]
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for i in range(interval, 0, -1):
                # \r과 함께 공백을 주어 이전 문장을 깨끗하게 지움
                msg = f"\r[{now_str}] 확인 완료. {i:4d}초 후 다시 시작..."
                print(msg.ljust(80), end="", flush=True)
                time.sleep(1)
            # print() 제거: 다음 '모니터링 시작' 로그가 이 줄을 덮어씀
        except KeyboardInterrupt: break
        except Exception as e:
            print(f"[{datetime.now()}] 오류 발생: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
