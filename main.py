# main.py
import ccxt
import pandas as pd
import numpy as np
import requests
import os
from datetime import datetime

def send_telegram(token, chat_id, text):
    if not token or not chat_id:
        print("⚠️ توکن یا آی‌دی تلگرام وجود ندارد.")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    max_length = 4096
    parts = []
    current_part = ""
    for line in text.split('\n'):
        if len(current_part) + len(line) + 1 > max_length:
            parts.append(current_part)
            current_part = line
        else:
            current_part += '\n' + line if current_part else line
    if current_part:
        parts.append(current_part)
    for part in parts:
        data = {"chat_id": chat_id, "text": part, "parse_mode": "Markdown"}
        try:
            r = requests.post(url, data=data)
            if r.status_code == 200:
                print("✅ پیام ارسال شد.")
            else:
                print(f"❌ خطا: {r.text}")
        except Exception as e:
            print(f"❌ خطای شبکه: {e}")

def main():
    symbol = os.getenv("SYMBOL") or "BTC/USDT"
    timeframe = os.getenv("TIMEFRAME") or "1h"
    since_str = os.getenv("SINCE") or "2024-01-01"
    until_str = os.getenv("UNTIL") or "2024-06-01"
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    print("✅ مرحله ۱: شروع اسکریپت")

    try:
        since_dt = datetime.strptime(since_str, "%Y-%m-%d")
        since_ms = int(since_dt.timestamp() * 1000)
        until_ms = int(datetime.strptime(until_str, "%Y-%m-%d").timestamp() * 1000)
    except Exception as e:
        print(f"❌ خطای تاریخ: {e}")
        return

    print(f"✅ مرحله ۲: دریافت داده {symbol} از {since_str}")

    try:
        exchange = ccxt.kucoin()
        data = exchange.fetch_ohlcv(symbol, timeframe, since=since_ms, limit=100)
        if not data:  # ← اینجا باید `data` باشد
            print("❌ داده‌ای یافت نشد.")
            return
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        print(f"✅ {len(df)} کندل دریافت شد.")

        report = f"""
📊 *سیگنال آزمایشی*
────────────────────────────
📌 نماد: `{symbol}`
🕒 تایم‌فریم: `{timeframe}`
📅 بازه: `{since_str} تا {until_str}`
✅ قیمت آخرین کندل: `{df['close'].iloc[-1]:.2f}`
        """
        print(report)
        send_telegram(telegram_token, telegram_chat_id, report)
    except Exception as e:
        print(f"❌ خطای کلی: {e}")
        send_telegram(telegram_token, telegram_chat_id, f"❌ خطای اجرایی: {e}")

if __name__ == "__main__":
    main()
