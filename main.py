import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime

# ———————————————————————
# تنظیمات
# ———————————————————————
SYMBOLS = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]  # فرمت KuCoin با خط تیره
TIMEFRAME = "15min"       # پشتیبانی شده: 1min, 3min, 15min, 1hour, 1day
CANDLES_LIMIT = 200       # تعداد کندل برای تحلیل

# 🔔 فقط اگر بخواهید سیگنال به تلگرام بفرستید
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"  # ← فقط اگر دارید، جایگزین کنید | اگر نه، خالی بگذارید
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"  # ← فقط اگر دارید

SEND_TELEGRAM = bool(TELEGRAM_TOKEN and TELEGRAM_CHAT_ID)

# ———————————————————————
# دریافت داده از API عمومی KuCoin
# ———————————————————————
def fetch_kucoin(symbol, timeframe="15min", limit=100):
    url = "https://api.kucoin.com/api/v1/market/candles"
    params = {
        "symbol": symbol,
        "type": timeframe,
        "limit": limit
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data["code"] == "200000":
            # داده‌ها به صورت [timestamp, open, close, high, low, volume, turnover]
            df = pd.DataFrame(
                data["data"],
                columns=["timestamp", "open", "close", "high", "low", "volume", "turnover"]
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit='s')
            df.set_index("timestamp", inplace=True)
            for col in ["open", "close", "high", "low", "volume"]:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df.sort_index(inplace=True)
            return df
        else:
            print(f"خطا در {symbol}: {data['msg']}")
            return None
    except Exception as e:
        print(f"خطا در ارتباط با KuCoin: {e}")
        return None

# ———————————————————————
# افزودن ویژگی‌های تکنیکال
# ———————————————————————
def add_technical_features(df):
    df = df.copy()

    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # MACD
    exp1 = df['close'].ewm(span=12).mean()
    exp2 = df['close'].ewm(span=26).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']

    # Bollinger Bands
    df['bb_middle'] = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
    df['bb_lower'] = df['bb_middle'] - (bb_std * 2)

    # ATR (ساده شده)
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = tr.rolling(14).mean()

    # تغییرات قیمت و حجم
    df['price_change'] = df['close'].pct_change(3)
    df['volume_change'] = df['volume'].pct_change()

    return df.dropna()

# ———————————————————————
# تشخیص سیگنال (ترکیب RSI + MACD + Bollinger)
# ———————————————————————
def get_signal(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # شرایط خرید
    buy_conditions = [
        last['rsi'] < 35,
        last['macd'] > last['macd_signal'],  # MACD صعودی
        prev['macd'] <= prev['macd_signal'],  # تقاطع رو به بالا
        last['close'] < last['bb_lower'],     # زیر باند پایین
    ]
    buy_score = sum(buy_conditions)

    # شرایط فروش
    sell_conditions = [
        last['rsi'] > 65,
        last['macd'] < last['macd_signal'],
        prev['macd'] >= prev['macd_signal'],
        last['close'] > last['bb_upper'],
    ]
    sell_score = sum(sell_conditions)

    if buy_score >= 3:
        return "🟢 خرید قوی", last['rsi'], last['macd_hist']
    elif buy_score == 2:
        return "🟡 خرید احتمالی", last['rsi'], last['macd_hist']
    elif sell_score >= 3:
        return "🔴 فروش قوی", last['rsi'], last['macd_hist']
    elif sell_score == 2:
        return "🟠 فروش احتمالی", last['rsi'], last['macd_hist']
    else:
        return "⚪ صبر کنید", last['rsi'], last['macd_hist']

# ———————————————————————
# ارسال به تلگرام (اختیاری)
# ———————————————————————
def send_telegram(message):
    if not SEND_TELEGRAM:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload, timeout=10)
    except:
        print("⚠️ ارسال تلگرام ناموفق")

# ———————————————————————
# اجرای اصلی
# ———————————————————————
def main():
    print(f"⏰ اجرا در: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    for symbol in SYMBOLS:
        try:
            print(f"دریافت داده: {symbol}")
            df = fetch_kucoin(symbol, TIMEFRAME, CANDLES_LIMIT)
            if df is None or len(df) < 50:
                print(f"داده کافی برای {symbol} نیست.")
                continue

            df = add_technical_features(df)
            signal, rsi, macd_hist = get_signal(df)
            close_price = df['close'].iloc[-1]

            message = f"""
📊 **سیگنال بازار - {symbol.replace('-', '/')}**
⏰ زمان: {df.index[-1].strftime('%Y-%m-%d %H:%M')}
🎯 سیگنال: {signal}
📌 قیمت: ${close_price:,.2f}
🔍 RSI: {rsi:.1f}
📈 MACD هیستوگرام: {macd_hist:.6f}
🔗 تحلیل: {len(df)} کندل 15 دقیقه‌ای
            """.strip()

            print(message)
            send_telegram(message)

        except Exception as e:
            error_msg = f"❌ خطا در پردازش {symbol}: {str(e)}"
            print(error_msg)
            send_telegram(error_msg)

if __name__ == "__main__":
    main()
