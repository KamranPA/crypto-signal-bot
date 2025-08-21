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
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, data=data)
        if r.status_code == 200:
            print("✅ پیام به تلگرام ارسال شد.")
        else:
            print(f"❌ خطا در ارسال: {r.text}")
    except Exception as e:
        print(f"❌ خطای شبکه: {e}")

def main():
    # دریافت ورودی‌ها
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
        print(f"❌ فرمت تاریخ اشتباه: {e}")
        return

    # دریافت داده
    try:
        exchange = ccxt.kucoin()
        all_data = []
        fetch_until = since_ms
        while fetch_until < until_ms + 86400000:
            data = exchange.fetch_ohlcv(symbol, timeframe, since=fetch_until, limit=1000)
            if not data:
                break
            all_data.extend(data)
            fetch_until = data[-1][0] + 1
            if data[-1][0] > until_ms:
                break
        df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df[(df['timestamp'] >= since_str) & (df['timestamp'] <= until_str)]
        if len(df) == 0:
            report = "❌ هیچ داده‌ای در بازه مشخص‌شده یافت نشد."
            print(report)
            send_telegram(telegram_token, telegram_chat_id, report)
            return
    except Exception as e:
        error_msg = f"❌ خطای دریافت داده: {e}"
        print(error_msg)
        send_telegram(telegram_token, telegram_chat_id, error_msg)
        return

    # محاسبه ATR
    df['tr'] = np.maximum(df['high'] - df['low'],
                          np.maximum(abs(df['high'] - df['close'].shift(1)),
                                     abs(df['low'] - df['close'].shift(1))))
    df['atr'] = df['tr'].rolling(14).mean()
    df.dropna(inplace=True)

    # سیگنال‌ها
    signals = []
    for i in range(len(df) - 1):
        row = df.iloc[i]
        nxt = df.iloc[i + 1]
        atr = row['atr']

        # Long
        if row['close'] < row['open'] and row['close'] < row['close'].rolling(20).mean().iloc[i] - 0.5 * atr:
            entry = row['close']
            sl = entry - 1.5 * atr
            tp = entry + 3.0 * atr
            result = "TP" if nxt['high'] >= tp else "SL" if nxt['low'] <= sl else "در جریان"
            signals.append(('Long', entry, sl, tp, result))

        # Short
        elif row['close'] > row['open'] and row['close'] > row['close'].rolling(20).mean().iloc[i] + 0.5 * atr:
            entry = row['close']
            sl = entry + 1.5 * atr
            tp = entry - 3.0 * atr
            result = "TP" if nxt['low'] <= tp else "SL" if nxt['high'] >= sl else "در جریان"
            signals.append(('Short', entry, sl, tp, result))

    # گزارش
    if signals:
        total = len(signals)
        tp_count = len([s for s in signals if s[4] == 'TP'])
        sl_count = len([s for s in signals if s[4] == 'SL'])
        win_rate = (tp_count / total) * 100

        report = f"""
📊 *بک‌تست معاملاتی*
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
            report += f"`[{sig[0]}]` ورود: `{sig[1]:.2f}` | SL: `{sig[2]:.2f}` | TP: `{sig[3]:.2f}` | نتیجه: `{sig[4]}`\n"
    else:
        report = "❌ هیچ سیگنالی تولید نشد."

    print("\n" + report)
    send_telegram(telegram_token, telegram_chat_id, report)

if __name__ == "__main__":
    main()
