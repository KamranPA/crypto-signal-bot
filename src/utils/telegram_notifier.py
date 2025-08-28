# src/utils/telegram_notifier.py

def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ خطای ارسال تلگرام: توکن یا آی‌دی تنظیم نشده است.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': text.replace('\\', ''),  # حذف \ از پیام
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
