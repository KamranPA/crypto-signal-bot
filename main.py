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

def fetch_coingecko_data(symbol, since_str, until_str):
    """
    دریافت داده تاریخی روزانه از CoinGecko
    """
    # تبدیل نماد: BTC/USDT → bitcoin
    symbol_map = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'BNB': 'binancecoin',
        'SOL': 'solana',
        'XRP': 'ripple'
    }
    gecko_id = symbol_map.get(symbol.split('/')[0].upper(), 'bitcoin')

    url = f"https://api.coingecko.com/api/v3/coins/{gecko_id}/market_chart"
    since_dt = datetime.strptime(since_str, "%Y-%m-%d")
    until_dt = datetime.strptime(until_str, "%Y-%m-%d")
    params = {
        'vs_currency': 'usd',
        'days': (until_dt - since_dt).days + 1,
        'interval': 'daily'
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            print(f"❌ خطای CoinGecko: {response.status_code} - {response.text}")
            return None

        data = response.json()
        prices = data['prices']  # [[timestamp, price], ...]

        df = pd.DataFrame(prices, columns=['timestamp', 'close'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['close'] = df['close'].astype(float)

        # ایجاد ستون‌های مصنوعی (برای شبیه‌سازی OHLC)
        df['open'] = df['close'].shift(1).fillna(df['close'] * 0.995)
        df['high'] = df['close'] * 1.02
        df['low'] = df['close'] * 0.98
        df['volume'] = np.random.uniform(1000, 10000, size=len(df))  # حجم مجازی

        # فیلتر بازه زمانی
        df = df[(df['timestamp'] >= since_str) & (df['timestamp'] <= until_str)]
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].copy()
        return df

    except Exception as e:
        print(f"❌ خطای دریافت داده از CoinGecko: {e}")
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
    except Exception as e:
        error_msg = f"❌ فرمت تاریخ اشتباه: {e}"
        print(error_msg)
        send_telegram(telegram_token, telegram_chat_id, error_msg)
        return

    # دریافت داده از CoinGecko
    try:
        df = fetch_coingecko_data(symbol, since_str, until_str)
        if df is None or len(df) == 0:
            report = "❌ هیچ داده‌ای از CoinGecko دریافت نشد. ممکن است شبکه مشکل داشته باشد."
            print(report)
            send_telegram(telegram_token, telegram_chat_id, report)
            return

        print(f"✅ {len(df)} کندل روزانه از CoinGecko دریافت شد.")
        print(f"📊 اولین قیمت: {df['close'].iloc[0]:.2f} | آخرین قیمت: {df['close'].iloc[-1]:.2f}")

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

        # Long
        if close < row['open'] and close < ma20 - 0.5 * atr and rsi < 30:
            if last_signal != 'Long':
                entry = close
                sl = entry - 1.5 * atr
                tp = entry + 3.0 * atr
                result = "TP" if next_row['high'] >= tp else "SL" if next_row['low'] <= sl else "در جریان"
                signals.append(('Long', round(entry, 2), round(sl, 2), round(tp, 2), result))
                last_signal = 'Long'

        # Short
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
📊 *گزارش بک‌تست معاملاتی (داده CoinGecko)*
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

    print("\n" + report)
    send_telegram(telegram_token, telegram_chat_id, report)

if __name__ == "__main__":
    main()
