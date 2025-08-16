# utils/telegram_bot.py
import requests
import json
import os

def send_telegram_signal(symbol, signal, entry, tp, sl, reason=""):
    try:
        with open('secrets/telegram_secrets.json') as f:
            secrets = json.load(f)
        token = secrets['telegram_token']
        chat_id = secrets['chat_id']

        message = (
            f"🚀 <b>سیگنال معاملاتی</b>\n"
            f"📌 <b>ارز:</b> {symbol}\n"
            f"🔹 <b>سیگنال:</b> {signal}\n"
            f"💰 <b>ورود:</b> {entry:.4f}\n"
            f"🎯 <b>هدف:</b> {tp:.4f}\n"
            f"🛑 <b>حد ضرر:</b> {sl:.4f}\n"
            f"📝 <b>دلیل:</b> {reason}"
        )

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        requests.post(url, data=payload)

    except Exception as e:
        print(f"[ERROR] ارسال سیگنال به تلگرام ناموفق: {e}")
