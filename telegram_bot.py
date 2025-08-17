# telegram_bot.py
import requests
from decouple import config

def send_telegram_message(message):
    try:
        # خواندن از .env یا محیط سیستم
        token = config('TELEGRAM_TOKEN')
        chat_id = config('TELEGRAM_CHAT_ID')

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, data=payload)

        if response.status_code == 200:
            print("✅ پیام به تلگرام ارسال شد.")
            return True
        else:
            print(f"❌ خطا در ارسال تلگرام: {response.text}")
            return False

    except Exception as e:
        print(f"❌ خطای ارسال تلگرام: {e}")
        return False
