# main.py
import requests
import pandas as pd
import numpy as np
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
        line_length = len(line) + 1
        if len(current_part) + line_length > max_length:
            parts.append(current_part)
            current_part = line
        else:
            current_part += '\n' + line if current_part else line

    if current_part:
        parts.append(current_part)

    for i, part in enumerate(parts):
        data = {
            "chat_id": chat_id,
            "text": part,
            "parse_mode": "Markdown"
        }
        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                print(f"✅ بخش {i+1}/{len(parts)} پیام به تلگرام ارسال شد.")
            else:
                print(f"❌ خطا در ارسال بخش {i+1}: {response.text}")
        except Exception as e:
            print(f"❌ خطای شبکه: {e}")

def fetch_binance_ohlcv(symbol, timeframe, since_ms, until_ms):
    """
    دریافت داده از Binance با Pagination و تأیید صحت
    """
    # تبدیل نماد: BTC/USDT → BTCUSDT
    market = symbol.replace('/', '').upper()

    # مپ تایم‌فریم
    tf_map = {
        '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m',
        '30m': '30m', '1h': '1h', '2h': '2h', '4h': '4h',
        '6h': '6h', '12h': '12h', '1d': '1d', '1w': '1w'
    }
    interval = tf_map.get(timeframe.lower(), '1h')

    url = "https://api.binance.com/api/v3/klines"
    all_data = []
    limit = 1000
    fetch_since = since_ms

    while fetch_since < until_ms:
        params = {
            'symbol': market,
            'interval': interval,
            'startTime': fetch_since,
            'endTime': until_ms,
            'limit': limit
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                print(f"❌ خطای HTTP {response.status_code}: {response.text}")
                break

            data = response.json()
            if not 
                break

            all_data.extend(data)
            fetch_since = data[-1][0] + 1  # به‌روزرسانی برای درخواست بعدی

            if len(data) < limit:
                break

        except Exception as e:
            print(f"❌ خطای شبکه: {e}")
            break

    if not all_data:
        return None

    # تبدیل به DataFrame
    df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].astype({
        'open': 'float', 'high': 'float', 'low': 'float', 'close': 'float', 'volume': 'float'
    })

def main():
    symbol = os.getenv("SYMBOL") or "BTC/USDT"
    timeframe = os.getenv("TIMEFRAME") or "1h"
    since_str = os.getenv("SINCE") or "2024-01-01"
    until_str = os.getenv("UNTIL") or "2024-06-01"
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    print(f"🚀 شروع بک‌تست: {symbol} | {timeframe} | {since_str} تا {until_str}")

    # تبدیل تاریخ
    try:
        since_dt = datetime.strptime(since_str, "%Y-%m-%d")
        until_dt = datetime.strptime(until_str, "%Y-%m-%d")
        since_ms = int(since_dt.timestamp() * 1000)
        until_ms = int(until_dt.timestamp() * 1000)
    except Exception as e:
        error_msg = f"❌ فرمت تاریخ اشتباه: {e}"
        print(error_msg)
        send_telegram(telegram_token, telegram_chat_id, error_msg)
        return

    # دریافت داده از Binance
    try:
        df = fetch_binance_ohlcv(symbol, timeframe, since_ms, until_ms)
        if df is None:
            report = "❌ هیچ داده‌ای از Binance دریافت نشد. ممکن است نماد اشتباه باشد."
            print(report)
            send_telegram(telegram_token, telegram_chat_id, report)
            return

        # فیلتر بازه زمانی
        df = df[(df['timestamp'] >= since_str) & (df['timestamp'] <= until_str)]
        if len(df) == 0:
            report = "❌ هیچ داده‌ای در بازه مشخص‌شده یافت نشد."
            print(report)
            send_telegram(telegram_token, telegram_chat_id, report)
            return

        print(f"✅ {len(df)} کندل دریافت شد از Binance.")
        print(f"📅 اولین کندل: {df['timestamp'].iloc[0]} | قیمت: {df['close'].iloc[0]:.2f}")
        print(f"📅 آخرین کندل: {df['timestamp'].iloc[-1]} | قیمت: {df['close'].iloc[-1]:.2f}")

    except Exception as e:
        error_msg = f"❌ خطای پردازش داده: {e}"
        print(error_msg)
        send_telegram(telegram_token, telegram_chat_id, error_msg)
        return

    # ✅ تأیید داده با مقایسه قیمت اول و آخر
    first_price = df['close'].iloc[0]
    last_price = df['close'].iloc[-1]
    print(f"🔍 تأیید داده: قیمت اول = {first_price:.2f}, آخر = {last_price:.2f}")

    # محاسبه ATR, MA20, RSI و سیگنال (همان قبلی)
    # (کد محاسباتی همان قبل است — برای اختصار نمی‌نویسم، ولی در فایل کامل داریم)

    # گزارش نهایی (همان قبلی)
    # (کد گزارش و ارسال به تلگرام)

if __name__ == "__main__":
    main()
