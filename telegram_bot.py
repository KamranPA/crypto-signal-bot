# telegram_bot.py
import requests
import os

def send_telegram_message(message):
    # خواندن توکن و چت آیدی از محیط یا متغیرهای سیستم
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("⚠️ توکن یا چت آیدی تلگرام تنظیم نشده است.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            return True
        else:
            print(f"❌ ارسال ناموفق: {response.text}")
            return False
    except Exception as e:
        print(f"❌ خطای ارسال تلگرام: {e}")
        return False
