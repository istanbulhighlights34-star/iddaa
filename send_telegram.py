#!/usr/bin/env python3
import sys
import json
import urllib.request
import urllib.parse

BOT_TOKEN = "9082147299:AAEQubL7YIyr4NPS_MAoT02xixUjQ_RtiD0"
CHAT_ID = "664321983"

def send_message(text, parse_mode="HTML"):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # Split text into chunks if it exceeds 4000 characters
    chunk_size = 4000
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    
    for chunk in chunks:
        payload = {
            "chat_id": CHAT_ID,
            "text": chunk,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data)
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode())
                if not result.get("ok"):
                    print(f"Telegram API Error: {result}", file=sys.stderr)
        except Exception as e:
            # Fallback without parse_mode if HTML entity error occurs
            if parse_mode:
                payload["parse_mode"] = ""
                data = urllib.parse.urlencode(payload).encode("utf-8")
                req = urllib.request.Request(url, data=data)
                try:
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        pass
                except Exception as inner_e:
                    print(f"Failed to send telegram message: {inner_e}", file=sys.stderr)
            else:
                print(f"Failed to send telegram message: {e}", file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:])
    else:
        msg = sys.stdin.read()
    if msg.strip():
        send_message(msg)
