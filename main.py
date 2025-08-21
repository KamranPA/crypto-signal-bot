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
        line_length = len(line) + 1  # +1 برای \n
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
            print(f"❌ خطای شبکه هنگام ارسال بخش {i+1}: {e}")

def fetch_binance_ohlcv(symbol, timeframe, since_ms, until_ms):
    """
    دریافت داده OHLCV از API عمومی Binance
    """
    # تبدیل نماد: BTC/USDT → BTCUSDT
    market = symbol.replace('/', '')

    # مپ تایم‌فریم به Binance
    tf_map = {
        '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m',
        '30m': '30m', '1h': '1h', '2h': '2h', '4h': '4h',
        '6h': '6h', '12h': '12h', '1d': '1d', '1w': '1w'
    }
    interval = tf_map.get(timeframe, '1h')

    url = "https://api.binance.com/api/v3/klines"
    params = {
        'symbol': market,
        'interval': interval,
        'startTime': since_ms,
        'endTime': until_ms,
        'limit': 1000
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data:
            return None

        ohlcv = []
        for item in data:
            ohlcv.append([
                int(item[0]),           # timestamp
                float(item[1]),         # open
                float(item[2]),         # high
                float(item[3]),         # low
                float(item[4]),         # close
                float(item[5])          # volume
            ])
        return ohlcv
    except Exception as e:
        print(f"❌ خطای دریافت داده از Binance: {e}")
        return None

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
        data = fetch_binance_ohlcv(symbol, timeframe, since_ms, until_ms)
        if not data:
            report = "❌ هیچ داده‌ای از Binance دریافت نشد. ممکن است نماد یا تایم‌فریم نامعتبر باشد."
            print(report)
            send_telegram(telegram_token, telegram_chat_id, report)
            return

        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # فیلتر بازه زمانی
        df = df[(df['timestamp'] >= since_str) & (df['timestamp'] <= until_str)]
        if len(df) == 0:
            report = "❌ هیچ داده‌ای در بازه مشخص‌شده یافت نشد. ممکن است بازه زمانی آینده باشد یا داده‌ای وجود نداشته باشد."
            print(report)
            send_telegram(telegram_token, telegram_chat_id, report)
            return

        print(f"✅ {len(df)} کندل دریافت شد از Binance.")
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
    last_signal = None  # جلوگیری از تکرار سیگنال

    for i in range(len(df) - 1):
        row = df.iloc[i]
        next_row = df.iloc[i + 1]
        close = row['close']
        atr = row['atr']
        ma20 = row['ma20']
        rsi = row['rsi']

        # سیگنال Long: قیمت زیر MA20، RSI<30، کندل نزولی
        if close < row['open'] and close < ma20 - 0.5 * atr and rsi < 30:
            if last_signal != 'Long':
                entry = close
                sl = entry - 1.5 * atr
                tp = entry + 3.0 * atr  # نسبت 2:1
                result = "TP" if next_row['high'] >= tp else "SL" if next_row['low'] <= sl else "در جریان"
                signals.append(('Long', round(entry, 2), round(sl, 2), round(tp, 2), result))
                last_signal = 'Long'

        # سیگنال Short: قیمت بالای MA20، RSI>70، کندل صعودی
        elif close > row['open'] and close > ma20 + 0.5 * atr and rsi > 70:
            if last_signal != 'Short':
                entry = close
                sl = entry + 1.5 * atr
                tp = entry - 3.0 * atr
                result = "TP" if next_row['low'] <= tp else "SL" if next_row['high'] >= sl else "در جریان"
                signals.append(('Short', round(entry, 2), round(sl, 2), round(tp, 2), result))
                last_signal = 'Short'

    # گزارش نهایی
    if signals:
        total = len(signals)
        tp_count = len([s for s in signals if s[4] == 'TP'])
        sl_count = len([s for s in signals if s[4] == 'SL'])
        win_rate = (tp_count / total) * 100 if total > 0 else 0

        report = f"""
📊 *گزارش بک‌تست معاملاتی (داده Binance)*
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
            report += f"`[{sig[0]}]` ورود: `{sig[1]}` | SL: `{sig[2]}` | TP: `{sig[3]}` | نتیجه: `{sig[4]}`\n"
    else:
        report = "❌ هیچ سیگنالی تولید نشد."

    # چاپ و ارسال گزارش
    print("\n" + report)
    send_telegram(telegram_token, telegram_chat_id, report)

if __name__ == "__main__":
    main()
