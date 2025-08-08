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
# توابع تحلیلی (EMA, RSI, Swing High/Low, Fibonacci)
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

def find_swing_high(high, window=5):
    for i in range(len(high) - window - 1, 0, -1):
        if all(high[i] > high[i - j] for j in range(1, window + 1)) and \
           all(high[i] > high[i + j] for j in range(1, window + 1)):
            return high[i]
    return None

def fibo_extension(entry, swing_point, ratio):
    return entry + ratio * (entry - swing_point)

def fibo_retracement(high, low, ratio):
    return high - ratio * (high - low)

# ——————————————————————————
# تشخیص سیگنال خرید (BUY)
# ——————————————————————————
def check_buy_signal(df):
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values
    open_price = df['open'].values

    if len(df) < 199:
        print("❌ [BUY] فیلتر ناکافی: داده کمتر از 199 کندل")
        return None

    # ——— فیلتر ۱: روند صعودی بلندمدت ———
    ema200 = ema(close, 200)
    if len(ema200) < 2:
        print("❌ [BUY] EMA200: داده کافی نیست")
        return None

    trend_ok = close[-1] > ema200[-1] and ema200[-1] > ema200[-2]
    print(f"🔍 [BUY-TREND] روند صعودی: {'[✓]' if trend_ok else '[✗]'} (قیمت={close[-1]:.0f}, EMA200={ema200[-1]:.0f})")
    if not trend_ok:
        if close[-1] <= ema200[-1]:
            print("❌ [BUY-TREND] رد شد: قیمت زیر EMA200")
        elif ema200[-1] <= ema200[-2]:
            print("❌ [BUY-TREND] رد شد: EMA200 در حال کاهش")
        return None

    # ——— فیلتر ۲: حجم بالا ———
    avg_vol = np.mean(volume[-21:-1])
    volume_ok = volume[-1] > avg_vol * 0.6 and close[-1] > open_price[-1]
    print(f"🔍 [BUY-VOL] حجم کافی: {'[✓]' if volume_ok else '[✗]'} (حجم={volume[-1]:.0f}, میانگین={avg_vol:.0f}, x{volume[-1]/avg_vol:.1f})")
    if not volume_ok:
        if volume[-1] <= avg_vol * 0.6:
            print(f"❌ [BUY-VOL] رد شد: حجم کم (ضریب: {volume[-1]/avg_vol:.1f}x)")
        else:
            print("❌ [BUY-VOL] رد شد: کندل قرمز است")
        return None

    # ——— فیلتر ۳: اصلاح + بازگشت RSI ———
    rsi_vals = rsi(close, 14)
    if len(rsi_vals) < 6:  # ✅ برای سیگنال خرید: حداقل 6 عنصر
        print("❌ [BUY] RSI: داده کافی نیست")
        return None

    rsi_ok = (38 < rsi_vals[-3] < 45) and (rsi_vals[-2] < rsi_vals[-3] < rsi_vals[-1]) and (rsi_vals[-1] < 50)
    print(f"🔍 [BUY-RSI] وضعیت RSI: {'[✓]' if rsi_ok else '[✗]'} (RSI[-3]={rsi_vals[-3]:.1f}, RSI[-1]={rsi_vals[-1]:.1f})")
    if not rsi_ok:
        if not (38 < rsi_vals[-3] < 45):
            print(f"❌ [BUY-RSI] رد شد: RSI[-3]={rsi_vals[-3]:.1f} خارج از 38-45")
        elif not (rsi_vals[-2] < rsi_vals[-3] < rsi_vals[-1]):
            print("❌ [BUY-RSI] رد شد: روند RSI صعودی نیست")
        elif rsi_vals[-1] >= 50:
            print(f"❌ [BUY-RSI] رد شد: RSI ≥ 50")
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
    print(f"🔍 [BUY-PAT] الگو: {'[✓] ' + pattern_name if pattern_ok else '[✗] ' + pattern_name}")
    if not pattern_ok:
        print("❌ [BUY-PAT] رد شد: الگوی بازگشتی نیست")
        return None

    # ——— محاسبه ورود، حد ضرر، حد سود ———
    entry = last['close']
    swing_low = find_swing_low(low, window=5)
    if not swing_low or swing_low >= entry:
        print(f"❌ [BUY] خطای حد ضرر: swing_low={swing_low}")
        return None

    stop_loss = swing_low * 0.997
    tp1 = fibo_extension(entry, swing_low, 1.618)
    tp2 = fibo_extension(entry, swing_low, 2.618)

    risk = entry - stop_loss
    rr1 = round((tp1 - entry) / risk, 2)
    rr2 = round((tp2 - entry) / risk, 2)

    return {
        "type": "BUY",
        "entry": round(entry, 2),
        "stop_loss": round(stop_loss, 2),
        "take_profit": [round(tp1, 2), round(tp2, 2)],
        "risk_reward": [rr1, rr2],
        "reason": "Trend + Volume + Pullback + Reversal Pattern"
    }

# ——————————————————————————
# تشخیص سیگنال فروش (SELL)
# ——————————————————————————
def check_sell_signal(df):
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values
    open_price = df['open'].values

    if len(df) < 199:
        print("❌ [SELL] فیلتر ناکافی: داده کمتر از 199 کندل")
        return None

    # ——— فیلتر ۱: روند نزولی بلندمدت ———
    ema200 = ema(close, 200)
    if len(ema200) < 2:
        print("❌ [SELL] EMA200: داده کافی نیست")
        return None

    trend_ok = close[-1] < ema200[-1] and ema200[-1] < ema200[-2]
    print(f"🔍 [SELL-TREND] روند نزولی: {'[✓]' if trend_ok else '[✗]'} (قیمت={close[-1]:.0f}, EMA200={ema200[-1]:.0f})")
    if not trend_ok:
        if close[-1] >= ema200[-1]:
            print("❌ [SELL-TREND] رد شد: قیمت بالای EMA200")
        elif ema200[-1] >= ema200[-2]:
            print("❌ [SELL-TREND] رد شد: EMA200 در حال افزایش")
        return None

    # ——— فیلتر ۲: حجم بالا ———
    avg_vol = np.mean(volume[-21:-1])
    volume_ok = volume[-1] > avg_vol * 0.6 and close[-1] < open_price[-1]
    print(f"🔍 [SELL-VOL] حجم کافی: {'[✓]' if volume_ok else '[✗]'} (حجم={volume[-1]:.0f}, میانگین={avg_vol:.0f}, x{volume[-1]/avg_vol:.1f})")
    if not volume_ok:
        if volume[-1] <= avg_vol * 0.6:
            print(f"❌ [SELL-VOL] رد شد: حجم کم (ضریب: {volume[-1]/avg_vol:.1f}x)")
        else:
            print("❌ [SELL-VOL] رد شد: کندل سبز است")
        return None

    # ——— فیلتر ۳: اصلاح + بازگشت RSI ———
    rsi_vals = rsi(close, 14)
    if len(rsi_vals) < 7:  # ✅ افزایش از 6 به 7 برای اطمینان از وجود rsi_vals[-3]
        print("❌ [SELL] RSI: داده کافی نیست")
        return None

    rsi_ok = (55 < rsi_vals[-3] < 62) and (rsi_vals[-2] > rsi_vals[-3] > rsi_vals[-1]) and (rsi_vals[-1] > 50)
    print(f"🔍 [SELL-RSI] وضعیت RSI: {'[✓]' if rsi_ok else '[✗]'} (RSI[-3]={rsi_vals[-3]:.1f}, RSI[-1]={rsi_vals[-1]:.1f})")
    if not rsi_ok:
        if not (55 < rsi_vals[-3] < 62):
            print(f"❌ [SELL-RSI] رد شد: RSI[-3]={rsi_vals[-3]:.1f} خارج از 55-62")
        elif not (rsi_vals[-2] > rsi_vals[-3] > rsi_vals[-1]):
            print("❌ [SELL-RSI] رد شد: روند RSI نزولی نیست")
        elif rsi_vals[-1] <= 50:
            print(f"❌ [SELL-RSI] رد شد: RSI ≤ 50")
        return None

    # ——— فیلتر ۴: الگوی بازگشتی ———
    last = df.iloc[-1]
    prev = df.iloc[-2]
    body = abs(last['open'] - last['close'])
    upper_wick = max(last['open'], last['close']) - last['high']

    is_shooting_star = upper_wick >= 2 * body and last['close'] < last['open']
    is_bearish_engulfing = last['close'] < prev['open'] and last['open'] > prev['close'] and last['close'] < last['open']

    pattern_ok = is_shooting_star or is_bearish_engulfing
    pattern_name = "Shooting Star" if is_shooting_star else ("Bearish Engulfing" if is_bearish_engulfing else "ندارد")
    print(f"🔍 [SELL-PAT] الگو: {'[✓] ' + pattern_name if pattern_ok else '[✗] ' + pattern_name}")
    if not pattern_ok:
        print("❌ [SELL-PAT] رد شد: الگوی بازگشتی نیست")
        return None

    # ——— محاسبه ورود، حد ضرر، حد سود ———
    entry = last['close']
    swing_high = find_swing_high(high, window=5)
    if not swing_high or swing_high <= entry:
        print(f"❌ [SELL] خطای حد ضرر: swing_high={swing_high}")
        return None

    stop_loss = swing_high * 1.003
    tp1 = fibo_retracement(swing_high, entry, 0.618)
    tp2 = fibo_retracement(swing_high, entry, 1.000)

    risk = stop_loss - entry
    rr1 = round((entry - tp1) / risk, 2)
    rr2 = round((entry - tp2) / risk, 2)

    return {
        "type": "SELL",
        "entry": round(entry, 2),
        "stop_loss": round(stop_loss, 2),
        "take_profit": [round(tp1, 2), round(tp2, 2)],
        "risk_reward": [rr1, rr2],
        "reason": "Downtrend + Volume + Pullback + Reversal Pattern"
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
        print("❌ خطا: توکن یا چت آیدی تنظیم نشده‌اند.")
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

    # ——— بررسی بسته شدن کندل قبل از آخرین کندل ———
    if len(df) < 2:
        print("❌ داده کافی نیست — حداقل 2 کندل لازم است")
        return

    prev_candle_start = df['datetime'].iloc[-2]
    prev_candle_end = prev_candle_start + timedelta(minutes=15)
    now = datetime.now(timezone.utc)
    time_since_close = (now - prev_candle_end).total_seconds()

    if time_since_close < 60:
        # ✅ ارسال پیام "سیستم فعال" هر یک ساعت
        last_hour_check_file = "last_hour_check.txt"
        last_check_time = None

        if os.path.exists(last_hour_check_file):
            with open(last_hour_check_file, "r") as f:
                try:
                    last_check_time = datetime.fromisoformat(f.read().strip())
                except:
                    last_check_time = None

        time_since_last_check = (now - last_check_time).total_seconds() if last_check_time else 3600

        if time_since_last_check >= 3300:  # هر 55 دقیقه
            send_telegram_message(
                TELEGRAM_TOKEN,
                TELEGRAM_CHAT_ID,
                "✅ سیستم فعال است — در حال نظارت بر بازار"
            )
            with open(last_hour_check_file, "w") as f:
                f.write(now.isoformat())

        print(f"⏳ کندل 15 دقیقه‌ای قبلی (شروع: {prev_candle_start.strftime('%H:%M')}) هنوز کمتر از 1 دقیقه از بسته شدن آن گذشته — اجرا متوقف شد")
        return

    print(f"✅ کندل 15 دقیقه‌ای (قبل از آخرین کندل) بسته شد: {prev_candle_start.strftime('%Y-%m-%d %H:%M')} UTC")

    # ——— بررسی سیگنال خرید ———
    df_for_signal = df.iloc[:-1].copy()
    print("🔍 شروع بررسی سیگنال خرید...")
    buy_signal = check_buy_signal(df_for_signal)

    if buy_signal:
        entry = buy_signal['entry']
        sl = buy_signal['stop_loss']
        tp1, tp2 = buy_signal['take_profit']
        rr1, rr2 = buy_signal['risk_reward']

        message = f"""
🟢 <b>سیگنال خرید BTC/USDT (15 دقیقه)</b>
📅 {now.strftime('%Y-%m-%d %H:%M:%S UTC')}
🎯 <b>ورود: {entry}</b>
⛔ حد ضرر: {sl}
✅ حد سود 1: {tp1} (RR: {rr1})
✅ حد سود 2: {tp2} (RR: {rr2})
📌 دلیل: {buy_signal['reason']}
        """
        send_telegram_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, message)

        signal_id = f"BUY_{now.strftime('%Y%m%d_%H%M%S')}"
        signals_db[signal_id] = {
            "type": "BUY",
            "entry": entry,
            "stop_loss": sl,
            "take_profit": [tp1, tp2],
            "status": "open",
            "entry_time": now.strftime('%Y-%m-%d %H:%M:%S UTC'),
            "tp1_hit": False,
            "tp2_hit": False,
            "sl_hit": False
        }
        save_signals(signals_db)
        print(f"✅ سیگنال خرید ذخیره شد: {signal_id}")

    # ——— بررسی سیگنال فروش ———
    print("🔍 شروع بررسی سیگنال فروش...")
    sell_signal = check_sell_signal(df_for_signal)

    if sell_signal:
        entry = sell_signal['entry']
        sl = sell_signal['stop_loss']
        tp1, tp2 = sell_signal['take_profit']
        rr1, rr2 = sell_signal['risk_reward']

        message = f"""
🔴 <b>سیگنال فروش BTC/USDT (15 دقیقه)</b>
📅 {now.strftime('%Y-%m-%d %H:%M:%S UTC')}
🎯 <b>ورود: {entry}</b>
⛔ حد ضرر: {sl}
✅ حد سود 1: {tp1} (RR: {rr1})
✅ حد سود 2: {tp2} (RR: {rr2})
📌 دلیل: {sell_signal['reason']}
        """
        send_telegram_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, message)

        signal_id = f"SELL_{now.strftime('%Y%m%d_%H%M%S')}"
        signals_db[signal_id] = {
            "type": "SELL",
            "entry": entry,
            "stop_loss": sl,
            "take_profit": [tp1, tp2],
            "status": "open",
            "entry_time": now.strftime('%Y-%m-%d %H:%M:%S UTC'),
            "tp1_hit": False,
            "tp2_hit": False,
            "sl_hit": False
        }
        save_signals(signals_db)
        print(f"✅ سیگنال فروش ذخیره شد: {signal_id}")

    # ——— چک کردن رسیدن به TP/SL ———
    current_price = df['close'].iloc[-1]
    updated = False
    for sid, s in signals_db.items():
        if s['status'] == 'open':
            if s['type'] == 'BUY':
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
            elif s['type'] == 'SELL':
                if current_price <= s['take_profit'][1]:
                    s['status'] = 'tp2_hit'
                    s['tp1_hit'] = True
                    s['tp2_hit'] = True
                    updated = True
                elif current_price <= s['take_profit'][0] and not s['tp1_hit']:
                    s['tp1_hit'] = True
                    updated = True
                elif current_price >= s['stop_loss']:
                    s['status'] = 'sl_hit'
                    s['sl_hit'] = True
                    updated = True
    if updated:
        save_signals(signals_db)

    # ——— گزارش روزانه ———
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
⏱ آخرین بررسی: {now_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}
        """
        send_telegram_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, report)

# ——————————————————————————
# اجرای برنامه
# ——————————————————————————
if __name__ == "__main__":
    main()
