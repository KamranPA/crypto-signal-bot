# src/utils/telegram_notifier.py

import requests
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MAX_LENGTH = 4096  # حداکثر طول پیام در تلگرام


def send_telegram_message(text):
    """
    ارسال یک پیام به تلگرام
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ خطای ارسال تلگرام: توکن یا آی‌دی تنظیم نشده است.")
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
            print(f"❌ ارسال ناموفق. کد: {response.status_code}, پاسخ: {response.text}")
            return False
    except Exception as e:
        print(f"❌ خطای ارسال: {e}")
        return False


def send_long_message(text):
    """
    ارسال پیام‌های طولانی به صورت چند قسمت
    """
    while len(text) > MAX_LENGTH:
        # پیدا کردن آخرین نقطه منطقی برای شکستن پیام (مثلاً قبل از شروع معامله جدید)
        part = text[:MAX_LENGTH]
        last_newline = part.rfind('\n')
        
        # اگر خط جدید وجود داشت، تا آخرین خط ببر
        if last_newline > 0:
            part = text[:last_newline + 1]  # شامل \n
            text = text[last_newline + 1:]
        else:
            # اگر خط جدید نبود، دقیقاً در حد ببر
            part = text[:MAX_LENGTH]
            text = text[MAX_LENGTH:]
        
        # ارسال قسمت
        if not send_telegram_message(part):
            print("❌ ارسال قسمتی از پیام ناموفق بود.")
            return False

    # ارسال باقی‌مانده
    if text.strip():
        return send_telegram_message(text)
    
    return True
