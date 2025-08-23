# main.py
import requests
import pandas as pd
import numpy as np
import os
from datetime import datetime

def send_telegram(token, chat_id, text):
    """
    ارسال پیام به تلگرام با پشتیبانی از پیام‌های طولانی
    """
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

def fetch_coinex_ohlcv(symbol, timeframe, since_ms, until_ms):
    """
    دریافت داده OHLCV از API عمومی CoinEx
    """
    # تبدیل نماد: BTC/USDT → btcusdt
    market = symbol.replace('/', '').lower()

    # مپ تایم‌فریم
    tf_map = {
        '1m': '1min', '3m': '3min', '5m': '5min', '15m': '15min',
        '30m': '30min', '1h': '1hour', '2h': '2hour', '4h': '4hour',
        '6h': '6hour', '12h': '12hour', '1d': '1day', '1w': '1week'
    }
    interval = tf_map.get(timeframe.lower(), '1hour')

    url = "https://api.coinex.com/v1/market/kline"
    all_data = []
    limit = 1000
    fetch_since = since_ms // 1000  # CoinEx زمان را به ثانیه می‌خواهد

    while fetch_since < until_ms // 1000:
        params = {
            'market': market,
            'type': interval,
            'limit': limit,
            'time_start': fetch_since
        }

        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code != 200:
                print(f"❌ خطا: {response.status_code} - {response.text}")
                break

            data = response.json()
            if data.get('code') != 0:
                print(f"❌ خطای CoinEx: {data.get('message')}")
                break

            klines = data.get('data', [])
            if not data:
                break

            count = len(klines)
            for item in klines:
                all_data.append([
                    int(item[0]) * 1000,  # زمان به میلی‌ثانیه
                    float(item[1]),       # open
                    float(item[3]),       # high
                    float(item[4]),       # low
                    float(item[2]),       # close
                    float(item[5])        # volume
                ])

            # به‌روزرسانی برای درخواست بعدی
            fetch_since = int(klines[-1][0]) + 1

            if count < limit:
                break

        except Exception as e:
            print(f"❌ خطای شبکه: {e}")
            break

    if not all_data:
        return None

    return all_data

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

    # دریافت داده از CoinEx
    try:
        data = fetch_coinex_ohlcv(symbol, timeframe, since_ms, until_ms)
        if not data:
            report = "❌ هیچ داده‌ای از CoinEx دریافت نشد. ممکن است نماد اشتباه باشد."
            print(report)
            send_telegram(telegram_token, telegram_chat_id, report)
            return

        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df[(df['timestamp'] >= since_str) & (df['timestamp'] <= until_str)]

        if len(df) == 0:
            report = "❌ هیچ داده‌ای در بازه زمانی یافت نشد."
            print(report)
            send_telegram(telegram_token, telegram_chat_id, report)
            return

        print(f"✅ {len(df)} کندل دریافت شد از CoinEx.")
        print(f"📊 اولین قیمت: {df['close'].iloc[0]:.2f}")
        print(f"📊 آخرین قیمت: {df['close'].iloc[-1]:.2f}")

    except Exception as e:
        error_msg = f"❌ خطای پردازش داده: {e}"
        print(error_msg)
        send_telegram(telegram_token, telegram_chat_id, error_msg)
        return

    # محاسبه ATR
    df['tr'] = np.maximum(
        df['high'] - df['low'],
        np.maximum(
            abs(df['high'] - df['close'].shift(1)),
            abs(df['low'] - df['close'].shift(1))
        )
    )
    df['atr'] = df['tr'].rolling(14).mean()

    # محاسبه MA20
    df['ma20'] = df['close'].rolling(20).mean()

    # محاسبه RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # حذف NaN
    df.dropna(inplace=True)

    # تولید سیگنال
    signals = []
    last_signal = None

    for i in range(len(df) - 1):
        row = df.iloc[i]
        close = row['close']
        atr = row['atr']
        ma20 = row['ma20']
        rsi = row['rsi']
        timestamp = row['timestamp']

        # سیگنال Long
        if close < row['open'] and close < ma20 - 0.5 * atr and rsi < 30:
            if last_signal != 'Long':
                entry = close
                sl = entry - 1.5 * atr
                tp = entry + 3.0 * atr
                result = "در جریان"
                # بررسی نتیجه بر اساس تمام کندل‌های بعدی
                for j in range(i + 1, len(df)):
                    if df['high'].iloc[j] >= tp:
                        result = "TP"
                        break
                    elif df['low'].iloc[j] <= sl:
                        result = "SL"
                        break
                signals.append((
                    'Long',
                    round(entry, 2),
                    round(sl, 2),
                    round(tp, 2),
                    result,
                    timestamp.strftime("%Y-%m-%d %H:%M")
                ))
                last_signal = 'Long'

        # سیگنال Short
        elif close > row['open'] and close > ma20 + 0.5 * atr and rsi > 70:
            if last_signal != 'Short':
                entry = close
                sl = entry + 1.5 * atr
                tp = entry - 3.0 * atr
                result = "در جریان"
                # بررسی نتیجه بر اساس تمام کندل‌های بعدی
                for j in range(i + 1, len(df)):
                    if df['low'].iloc[j] <= tp:
                        result = "TP"
                        break
                    elif df['high'].iloc[j] >= sl:
                        result = "SL"
                        break
                signals.append((
                    'Short',
                    round(entry, 2),
                    round(sl, 2),
                    round(tp, 2),
                    result,
                    timestamp.strftime("%Y-%m-%d %H:%M")
                ))
                last_signal = 'Short'

    # گزارش نهایی
    if signals:
        total = len(signals)
        tp_count = len([s for s in signals if s[4] == 'TP'])
        sl_count = len([s for s in signals if s[4] == 'SL'])
        ongoing_count = len([s for s in signals if s[4] == 'در جریان'])
        win_rate = (tp_count / total) * 100 if total > 0 else 0

        report = f"""
📊 *گزارش بک‌تست معاملاتی (داده CoinEx)*
────────────────────────────
📌 *نماد:* `{symbol}`
🕒 *تایم‌فریم:* `{timeframe}`
📅 *بازه:* `{since_str} تا {until_str}`
📊 *تعداد معاملات:* `{total}`
✅ *حد سود:* `{tp_count}`
❌ *حد ضرر:* `{sl_count}`
🔄 *در جریان:* `{ongoing_count}`
📈 *نرخ برد:* `{win_rate:.1f}%`
🎯 *نسبت ریسک به ریوارد:* `1:2`
────────────────────────────
        """
        for sig in signals:
            report += f"`[{sig[0]}]` 📅 {sig[5]} | ورود: `{sig[1]}` | SL: `{sig[2]}` | TP: `{sig[3]}` | نتیجه: `{sig[4]}`\n"
    else:
        report = "❌ هیچ سیگنالی تولید نشد."

    print("\n" + report)
    send_telegram(telegram_token, telegram_chat_id, report)

if __name__ == "__main__":
    main()
