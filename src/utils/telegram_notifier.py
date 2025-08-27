# src/utils/telegram_notifier.py

import requests
import os

# خواندن توکن و آی‌دی از متغیرهای محیطی
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram_message(text):
    """
    ارسال پیام به تلگرام
    :param text: متن پیام (با پشتیبانی از HTML)
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ خطای ارسال تلگرام: TELEGRAM_BOT_TOKEN یا TELEGRAM_CHAT_ID تنظیم نشده است.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }

    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            return True
        else:
            print(f"❌ ارسال پیام ناموفق. کد وضعیت: {response.status_code}, پاسخ: {response.text}")
            return False
    except Exception as e:
        print(f"❌ خطای ارسال تلگرام: {e}")
        return False


def send_long_message(text, max_length=4096):
    """
    ارسال پیام‌های طولانی به صورت چند بخشی
    """
    while len(text) > max_length:
        # پیدا کردن آخرین خط‌جدید قبل از حد
        part = text[:max_length]
        last_newline = part.rfind('\n')
        if last_newline != -1 and len(text) > max_length:
            part = text[:last_newline]
            text = text[last_newline + 1:]
        else:
            part = text[:max_length]
            text = text[max_length:]
        
        if not send_telegram_message(part):
            return False  # اگر ارسال نشد، متوقف شو

    if text.strip():
        return send_telegram_message(text)
    
    return True
