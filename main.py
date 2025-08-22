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

def fetch_binance_testnet_ohlcv(symbol, timeframe, since_ms, until_ms):
    """
    دریافت داده OHLCV از Binance Testnet Future API
    """
    market = symbol.replace('/', '').upper()

    tf_map = {
        '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m',
        '30m': '30m', '1h': '1h', '2h': '2h', '4h': '4h',
        '6h': '6h', '12h': '12h', '1d': '1d', '1w': '1w'
    }
    interval = tf_map.get(timeframe.lower(), '1h')

    url = "https://testnet.binancefuture.com/fapi/v1/klines"
    all_data = []
    limit = 1000
    fetch_since = since_ms

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    while fetch_since < until_ms:
        params = {
            'symbol': market,
            'interval': interval,
            'startTime': fetch_since,
            'endTime': until_ms,
            'limit': limit
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"❌ خطا: {response.status_code} - {response.text}")
                break

            data = response.json()
            if not data:
                print("⚠️ پاسخ خالی است.")
                break

            count = len(data)
            all_data.extend(data)
            print(f"✅ {count} کندل دریافت شد.")
            fetch_since = data[-1][0] + 1

            if count < limit:
                break

        except Exception as e:
            print(f"❌ خطای شبکه: {e}")
            break

    if not all_data:
        return None

    ohlcv = []
    for item in all_data:
        ohlcv.append([
            int(item[0]),
            float(item[1]),
            float(item[2]),
            float(item[3]),
            float(item[4]),
            float(item[5])
        ])
    return ohlcv

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

    # دریافت داده از Testnet Future
    try:
        data = fetch_binance_testnet_ohlcv(symbol, timeframe, since_ms, until_ms)
        if not data:
            report = "❌ هیچ داده‌ای از Binance Testnet Future دریافت نشد."
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

        print(f"✅ {len(df)} کندل دریافت شد از Binance Testnet Future.")
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
        next_row = df.iloc[i + 1]
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
                # ✅ بررسی نتیجه بر اساس تمام کندل‌های بعدی
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
                # ✅ بررسی نتیجه بر اساس تمام کندل‌های بعدی
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
        win_rate = (tp_count / total) * 100 if total > 0 else 0

        report = f"""
📊 *گزارش بک‌تست معاملاتی (داده Binance Testnet Future)*
────────────────────────────
📌 *نماد:* `{symbol}`
🕒 *تایم‌فریم:* `{timeframe}`
📅 *بازه:* `{since_str} تا {until_str}`
📊 *تعداد معاملات:* `{total}`
✅ *حد سود:* `{tp_count}`
❌ *حد ضرر:* `{sl_count}`
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
