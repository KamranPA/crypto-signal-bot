# main.py
import ccxt
import pandas as pd
import json
import os
from datetime import datetime, timezone, timedelta
import requests
import numpy as np

# ——————————————————————————
# تنظیمات
# ——————————————————————————
SYMBOL = "BTC/USDT"
TIMEFRAME = "15m"
LIMIT = 200
SIGNALS_FILE = "signals.json"

# دریافت توکن و چت آیدی از GitHub Secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# بارگذاری وضعیت سیگنال‌های قبلی
def load_signals():
    if os.path.exists(SIGNALS_FILE):
        with open(SIGNALS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_signals(data):
    with open(SIGNALS_FILE, "w") as f:
        json.dump(data, f, indent=2)

signals_db = load_signals()

# ——————————————————————————
# ارسال پیام به تلگرام با requests
# ——————————————————————————
def send_telegram_message(token, chat_id, message):
    if not token or not chat_id:
        print("❌ خطا: توکن یا چت آیدی تنظیم نشده‌اند.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, data=payload, timeout=15)
        if response.status_code == 200:
            print("✅ پیام با موفقیت به تلگرام ارسال شد")
        else:
            print(f"❌ خطا در ارسال پیام: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ خطا در اتصال به تلگرام: {e}")

# ——————————————————————————
# توابع تحلیلی (EMA, RSI, Swing Low, Fibonacci)
# ——————————————————————————
def ema(data, period):
    return pd.Series(data).ewm(span=period, adjust=False).mean().values

def rsi(data, period=14):
    delta = np.diff(data)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(period).mean()
    avg_loss = pd.Series(loss).rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def find_swing_low(low, window=5):
    for i in range(len(low) - window - 1, 0, -1):
        if all(low[i] < low[i - j] for j in range(1, window + 1)) and \
           all(low[i] < low[i + j] for j in range(1, window + 1)):
            return low[i]
    return None

def fibo_extension(entry, swing_low, ratio):
    return entry + ratio * (entry - swing_low)

# ——————————————————————————
# بررسی بسته شدن کندل 15 دقیقه‌ای
# ——————————————————————————
def is_candle_closed(candle_time):
    now = datetime.now(timezone.utc)
    candle_end = candle_time + timedelta(minutes=15)
    return (now - candle_end).total_seconds() > 60

# ——————————————————————————
# تشخیص سیگنال خرید (فیلتر چندلایه + لاگ دقیق)
# ——————————————————————————
def check_signal(df):
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values
    open_price = df['open'].values

    if len(df) < 200:
        print("❌ فیلتر ناکافی: داده کمتر از 200 کندل")
        return None

    # ——— فیلتر ۱: روند صعودی بلندمدت ———
    ema200 = ema(close, 200)
    trend_ok = close[-1] > ema200[-1] and ema200[-1] > ema200[-2]
    print(f"🔍 [TREND] روند صعودی: {'[✓]' if trend_ok else '[✗]'} (قیمت={close[-1]:.0f}, EMA200={ema200[-1]:.0f})")

    if not trend_ok:
        print("❌ سیگنال متوقف شد: روند صعودی نیست")
        return None

    # ——— فیلتر ۲: حجم بالا ———
    avg_vol = np.mean(volume[-21:-1])
    volume_ok = volume[-1] > avg_vol * 1.8 and close[-1] > open_price[-1]
    print(f"🔍 [VOLUME] حجم کافی: {'[✓]' if volume_ok else '[✗]'} (حجم={volume[-1]:.0f}, میانگین={avg_vol:.0f}, x{volume[-1]/avg_vol:.1f})")

    if not volume_ok:
        print("❌ سیگنال متوقف شد: حجم کافی نیست یا کندل قرمز است")
        return None

    # ——— فیلتر ۳: اصلاح + بازگشت RSI ———
    rsi_vals = rsi(close, 14)
    if len(rsi_vals) < 4:
        print("❌ فیلتر RSI: داده کافی نیست")
        return None

    rsi_ok = (38 < rsi_vals[-3] < 45) and (rsi_vals[-2] < rsi_vals[-3] < rsi_vals[-1]) and (rsi_vals[-1] < 50)
    print(f"🔍 [RSI] وضعیت RSI: {'[✓]' if rsi_ok else '[✗]'} (RSI[-3]={rsi_vals[-3]:.1f}, RSI[-1]={rsi_vals[-1]:.1f})")

    if not rsi_ok:
        print("❌ سیگنال متوقف شد: شرایط RSI برقرار نیست")
        return None

    # ——— فیلتر ۴: الگوی بازگشتی ———
    last = df.iloc[-1]
    prev = df.iloc[-2]
    body = abs(last['open'] - last['close'])
    lower_wick = last['low'] - min(last['open'], last['close'])

    is_hammer = lower_wick >= 2 * body and last['close'] > last['open']
    is_bullish_engulfing = last['close'] > prev['open'] and last['open'] < prev['close'] and last['close'] > last['open']

    pattern_ok = is_hammer or is_bullish_engulfing
    pattern_name = "Hammer" if is_hammer else ("Bullish Engulfing" if is_bullish_engulfing else "ندارد")
    print(f"🔍 [PATTERN] الگوی بازگشتی: {'[✓] ' + pattern_name if pattern_ok else '[✗] ' + pattern_name}")

    if not pattern_ok:
        print("❌ سیگنال متوقف شد: الگوی بازگشتی تشخیص داده نشد")
        return None

    # ——— همه فیلترها عبور داده شد ———
    print("✅ تمام فیلترها عبور داده شدند — سیگنال معتبر است")

    # ——— محاسبه ورود، حد ضرر، حد سود ———
    entry = last['close']
    swing_low = find_swing_low(low, window=5)

    if not swing_low or swing_low >= entry:
        print(f"❌ خطای محاسبه حد ضرر: swing_low={swing_low}, entry={entry}")
        return None

    stop_loss = swing_low * 0.997
    tp1 = fibo_extension(entry, swing_low, 1.618)
    tp2 = fibo_extension(entry, swing_low, 2.618)

    risk = entry - stop_loss
    rr1 = round((tp1 - entry) / risk, 2)
    rr2 = round((tp2 - entry) / risk, 2)

    return {
        "entry": round(entry, 2),
        "stop_loss": round(stop_loss, 2),
        "take_profit": [round(tp1, 2), round(tp2, 2)],
        "risk_reward": [rr1, rr2],
        "reason": "Trend + Volume + Pullback + Reversal Pattern"
    }

# ——————————————————————————
# تابع اصلی
# ——————————————————————————
def main():
    print("🚀 شروع اجرای سیستم تولید سیگنال BTC/USDT (15 دقیقه)")

    # ——— دیباگ متغیرهای محیطی ———
    print(f"🔹 TELEGRAM_TOKEN: {'[موجود]' if TELEGRAM_TOKEN else '[ناقص - تنظیم نشده]'}")
    print(f"🔹 TELEGRAM_CHAT_ID: {TELEGRAM_CHAT_ID or '[ناقص]'}")

    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ خطا: توکن یا چت آیدی تنظیم نشده‌اند. لطفاً در GitHub Secrets بررسی کنید.")
        return

    # ——— دریافت داده از KuCoin ———
    try:
        exchange = ccxt.kucoin()
        ohlcv = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=LIMIT)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        print(f"✅ داده از KuCoin دریافت شد: {len(df)} کندل")
    except Exception as e:
        print(f"❌ خطای دریافت داده از KuCoin: {e}")
        return

    # ——— بررسی بسته شدن کندل ———
    last_candle_time = df['datetime'].iloc[-1]
    if not is_candle_closed(last_candle_time):
        # ارسال پیام "سیستم فعال" هر یک ساعت
        if datetime.now(timezone.utc).minute % 60 == 0:
            send_telegram_message(
                TELEGRAM_TOKEN,
                TELEGRAM_CHAT_ID,
                "✅ سیستم فعال است — در حال نظارت بر بازار"
            )
        return

    print(f"✅ کندل 15 دقیقه‌ای بسته شد: {last_candle_time.strftime('%Y-%m-%d %H:%M')} UTC")

    # ——— بررسی سیگنال ———
    signal = check_signal(df)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if signal:
        entry = signal['entry']
        sl = signal['stop_loss']
        tp1, tp2 = signal['take_profit']
        rr1, rr2 = signal['risk_reward']

        message = f"""
🚀 <b>سیگنال جدید BTC/USDT (15 دقیقه)</b>
📅 {now}
🎯 <b>ورود: {entry}</b>
⛔ حد ضرر: {sl}
✅ حد سود 1: {tp1} (RR: {rr1})
✅ حد سود 2: {tp2} (RR: {rr2})
📌 دلیل: {signal['reason']}
        """
        send_telegram_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, message)

        # ذخیره سیگنال
        signal_id = f"BTC_{now.replace(' ', '_').replace(':', '')}"
        signals_db[signal_id] = {
            "type": "BUY",
            "entry": entry,
            "stop_loss": sl,
            "take_profit": [tp1, tp2],
            "status": "open",
            "entry_time": now,
            "tp1_hit": False,
            "tp2_hit": False,
            "sl_hit": False
        }
        save_signals(signals_db)
        print(f"✅ سیگنال ذخیره شد: {signal_id}")

    # ——— چک کردن رسیدن به TP/SL ———
    current_price = df['close'].iloc[-1]
    updated = False
    for sid, s in signals_db.items():
        if s['status'] == 'open':
            if current_price >= s['take_profit'][1]:
                s['status'] = 'tp2_hit'
                s['tp1_hit'] = True
                s['tp2_hit'] = True
                updated = True
            elif current_price >= s['take_profit'][0] and not s['tp1_hit']:
                s['tp1_hit'] = True
                updated = True
            elif current_price <= s['stop_loss']:
                s['status'] = 'sl_hit'
                s['sl_hit'] = True
                updated = True
    if updated:
        save_signals(signals_db)

    # ——— گزارش روزانه (UTC 00:00) ———
    now_dt = datetime.now(timezone.utc)
    if now_dt.hour == 0 and 0 <= now_dt.minute < 15:
        total = len([s for s in signals_db.values() if 'entry_time' in s])
        tp_hit = len([s for s in signals_db.values() if s.get('tp1_hit')])
        sl_hit = len([s for s in signals_db.values() if s.get('sl_hit')])
        active = len([s for s in signals_db.values() if s['status'] == 'open'])

        report = f"""
📊 <b>گزارش روزانه سیگنال‌ها</b>
📆 {now_dt.strftime('%Y-%m-%d')}
🔹 تعداد کل سیگنال‌ها: {total}
🟢 رسیدن به حد سود: {tp_hit}
🔴 رسیدن به حد ضرر: {sl_hit}
🟡 در حال اجرا: {active}
⏱ آخرین بررسی: {now}
        """
        send_telegram_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, report)

# ——————————————————————————
# اجرای برنامه
# ——————————————————————————
if __name__ == "__main__":
    main()
