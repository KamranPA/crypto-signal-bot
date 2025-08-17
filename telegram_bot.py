# telegram_bot.py
import requests
from decouple import config

def send_telegram_message(message):
    try:
        token = config('TELEGRAM_TOKEN')
        chat_id = config('TELEGRAM_CHAT_ID')
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        response = requests.post(url, data=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ ارسال تلگرام شکست خورد: {e}")
        return False
