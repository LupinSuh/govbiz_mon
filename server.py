import os
import json
from fastapi import FastAPI, Request
from dotenv import load_dotenv, set_key
import uvicorn

app = FastAPI()

# .env 파일 경로
ENV_FILE = ".env"

def get_keywords():
    load_dotenv(override=True)
    keywords_str = os.getenv("KEYWORDS", "")
    return [k.strip() for k in keywords_str.split(",") if k.strip()]

def add_keyword(new_keyword):
    keywords = get_keywords()
    if new_keyword not in keywords:
        keywords.append(new_keyword)
        new_keywords_str = ", ".join(keywords)
        # .env 파일 업데이트
        set_key(ENV_FILE, "KEYWORDS", new_keywords_str)
        return True, f"✅ 키워드 '{new_keyword}'가 추가되었습니다."
    return False, f"⚠️ 키워드 '{new_keyword}'는 이미 존재합니다."

def list_keywords():
    keywords = get_keywords()
    if not keywords:
        return "현재 등록된 키워드가 없습니다."
    return "현재 키워드 목록:\n" + "\n".join([f"- {k}" for k in keywords])

@app.post("/google-chat")
async def google_chat_handler(request: Request):
    data = await request.json()
    
    # 메시지 타입 확인
    if data.get("type") == "ADDED_TO_SPACE":
        return {"text": "반갑습니다! 검색어 모니터링 봇입니다. '추가 [검색어]' 또는 '목록'이라고 입력해 보세요."}
    
    if data.get("type") == "MESSAGE":
        message_text = data.get("message", {}).get("text", "").strip()
        
        # 멘션 제거 (봇이 멘션된 경우)
        if message_text.startswith("@"):
            parts = message_text.split(" ", 1)
            if len(parts) > 1:
                message_text = parts[1].strip()

        if message_text.startswith("추가 "):
            keyword = message_text.replace("추가 ", "", 1).strip()
            success, msg = add_keyword(keyword)
            return {"text": msg}
        
        elif message_text == "목록":
            return {"text": list_keywords()}
        
        else:
            return {"text": "명령어를 이해하지 못했습니다.\n- 추가 [검색어]\n- 목록"}

    return {}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
