# main.py
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# -----------------------------------------
# ۱. دریافت ورودی از کاربر
# -----------------------------------------
print("🚀 سیستم بک‌تست دستی معاملاتی (Long/Short) - ارزهای دیجیتال")
print("────────────────────────────────────────────────────")

symbol = input("🔸 نماد (مثلاً BTC/USDT): ").strip().upper()
timeframe = input("⏰ تایم‌فریم (مثلاً 15m, 1h): ").strip()
since_str = input("📅 تاریخ شروع (مثلاً 2024-01-01): ").strip()

try:
    since_dt = datetime.strptime(since_str, "%Y-%m-%d")
    since_ms = int(since_dt.timestamp() * 1000)
except ValueError:
    print("❌ فرمت تاریخ نامعتبر است. از فرمت YYYY-MM-DD استفاده کنید.")
    exit()

# -----------------------------------------
# ۲. دریافت داده از صرافی (KuCoin یا Binance)
# -----------------------------------------
print(f"\n📥 در حال دریافت داده‌ها برای {symbol} در تایم‌فریم {timeframe}...")
try:
    exchange = ccxt.kucoin()
    # exchange = ccxt.binance()  # می‌توانید تعویض کنید
    data = exchange.fetch_ohlcv(symbol, timeframe, since=since_ms, limit=1000)
    if len(data) == 0:
        print("❌ داده‌ای یافت نشد. نماد یا تایم‌فریم را بررسی کنید.")
        exit()

    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
except Exception as e:
    print(f"❌ خطای دریافت داده: {e}")
    exit()

# -----------------------------------------
# ۳. محاسبه ATR و ترند (برای حد سود/ضرر)
# -----------------------------------------
def calculate_atr(df, window=14):
    df['tr0'] = df['high'] - df['low']
    df['tr1'] = abs(df['high'] - df['close'].shift(1))
    df['tr2'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
    df['atr'] = df['tr'].rolling(window).mean()
    return df

df = calculate_atr(df)
df.dropna(inplace=True)

# -----------------------------------------
# ۴. سیگنال‌های تکنیکال ساده (Long/Short)
# -----------------------------------------
signals = []

for i in range(2, len(df) - 1):
    prev = df.iloc[i - 2]
    curr = df.iloc[i]
    next_candle = df.iloc[i + 1]  # برای بررسی نتیجه

    # شرایط ساده برای Long
    if curr['close'] > curr['open'] and curr['close'] < curr['close'].rolling(20).mean() - 0.5 * curr['atr']:
        price = curr['close']
        atr = curr['atr']
        sl = price - 1.5 * atr
        tp = price + 3.0 * atr  # نسبت 2:1 (3/1.5 = 2)
        outcome = None

        # بررسی نتیجه در کندل بعدی
        if next_candle['low'] <= sl:
            outcome = "SL"
        elif next_candle['high'] >= tp:
            outcome = "TP"

        signals.append({
            "type": "Long",
            "entry": round(price, 2),
            "sl": round(sl, 2),
            "tp": round(tp, 2),
            "time": curr['timestamp'],
            "result": outcome
        })

    # شرایط ساده برای Short
    elif curr['close'] < curr['open'] and curr['close'] > curr['close'].rolling(20).mean() + 0.5 * curr['atr']:
        price = curr['close']
        atr = curr['atr']
        sl = price + 1.5 * atr
        tp = price - 3.0 * atr
        outcome = None

        if next_candle['high'] >= sl:
            outcome = "SL"
        elif next_candle['low'] <= tp:
            outcome = "TP"

        signals.append({
            "type": "Short",
            "entry": round(price, 2),
            "sl": round(sl, 2),
            "tp": round(tp, 2),
            "time": curr['timestamp'],
            "result": outcome
        })

# -----------------------------------------
# ۵. گزارش نهایی
# -----------------------------------------
if len(signals) == 0:
    print("\n❌ هیچ سیگنالی یافت نشد.")
else:
    df_signals = pd.DataFrame(signals)
    total = len(df_signals)
    tp_count = len(df_signals[df_signals['result'] == 'TP'])
    sl_count = len(df_signals[df_signals['result'] == 'SL'])
    win_rate = (tp_count / total) * 100

    print("\n" + "📊 گزارش بک‌تست".center(50))
    print("─" * 50)
    print(f"نماد: {symbol}")
    print(f"تایم‌فریم: {timeframe}")
    print(f"بازه: {since_str} تا {df['timestamp'].iloc[-1].date()}")
    print(f"تعداد کل سیگنال‌ها: {total}")
    print(f"تعداد حد سود (TP): {tp_count}")
    print(f"تعداد حد ضرر (SL): {sl_count}")
    print(f"نرخ برد: {win_rate:.1f}%")
    print(f"نسبت ریسک به ریوارد: 1:2")
    print("─" * 50)

    # نمایش جزئیات معاملات
    for _, sig in df_signals.iterrows():
        print(f"[{sig['time']}] {sig['type']} | ورود: {sig['entry']} | SL: {sig['sl']} | TP: {sig['tp']} | نتیجه: {sig['result']}")
