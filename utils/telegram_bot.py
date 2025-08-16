# utils/telegram_bot.py
import requests
import json
import os
import logging

logger = logging.getLogger(__name__)

def send_telegram_signal(symbol, signal, entry, tp, sl, reason=""):
    try:
        # بررسی وجود فایل مخفی
        if not os.path.exists('secrets/telegram_secrets.json'):
            logger.warning("⚠️ فایل مخفی تلگرام وجود ندارد. ارسال لغو شد.")
            return

        with open('secrets/telegram_secrets.json') as f:
            secrets = json.load(f)

        token = secrets.get('telegram_token')
        chat_id = secrets.get('chat_id')

        if not token or not chat_id:
            logger.error("❌ توکن یا chat_id در فایل مخفی یافت نشد.")
            return

        message = (
            f"🚀 <b>سیگنال معاملاتی</b>\n"
            f"📌 <b>ارز:</b> {symbol}\n"
            f"🔹 <b>سیگنال:</b> {signal}\n"
            f"💰 <b>ورود:</b> {entry:.6f}\n"
            f"🎯 <b>هدف:</b> {tp:.6f}\n"
            f"🛑 <b>حد ضرر:</b> {sl:.6f}\n"
            f"📝 <b>دلیل:</b> {reason}"
        )

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }

        response = requests.post(url, data=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"✅ سیگنال به تلگرام ارسال شد: {symbol} | {signal}")
        else:
            logger.error(f"❌ ارسال سیگنال ناموفق. کد: {response.status_code}, پاسخ: {response.text}")

    except Exception as e:
        logger.error(f"🚨 خطا در ارسال به تلگرام: {e}")
