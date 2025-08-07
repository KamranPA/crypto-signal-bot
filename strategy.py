# strategy.py
from indicators import *
import numpy as np

def check_signal(df):
    """
    df: DataFrame با ستون‌های ['open', 'high', 'low', 'close', 'volume']
    خروجی: dict سیگنال یا None
    """
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values

    if len(df) < 200:
        return None

    # لایه ۱: روند بلندمدت (EMA200 صعودی)
    ema200 = ema(close, 200)
    if close[-1] <= ema200[-1] or ema200[-1] <= ema200[-2]:
        return None

    # لایه ۲: حجم بالا (حداقل 1.8 برابر میانگین 20 کندل)
    avg_vol = np.mean(volume[-21:-1])
    if volume[-1] <= avg_vol * 1.8 or close[-1] <= open[-1]:
        return None

    # لایه ۳: اصلاح و بازگشت RSI
    rsi_vals = rsi(close, 14)
    if len(rsi_vals) < 4 or rsi_vals[-1] >= 50:
        return None
    if not (rsi_vals[-3] < 45 and rsi_vals[-3] > 38):
        return None
    if not (rsi_vals[-2] < rsi_vals[-3] and rsi_vals[-1] > rsi_vals[-2]):
        return None

    # لایه ۴: الگوی قیمت (Hammer یا Bullish Engulfing)
    last_candle = df.iloc[-1]
    prev_candle = df.iloc[-2]
    
    # Hammer: ویک پایین بلند، بدنه کوچک، باز و بست در بالای محدوده
    body = abs(last_candle['open'] - last_candle['close'])
    lower_wick = last_candle['low'] - min(last_candle['open'], last_candle['close'])
    if not (lower_wick > 2 * body and last_candle['close'] > last_candle['open']):
        # بررسی Bullish Engulfing
        if not (last_candle['close'] > prev_candle['open'] and 
                last_candle['open'] < prev_candle['close'] and 
                last_candle['close'] > last_candle['open']):
            return None

    # لایه ۵: کندل کاملاً بسته شده (حداقل 1 دقیقه از زمان بسته شدن گذشته)
    # (در main.py بررسی می‌شود)

    # ✅ همه فیلترها عبور داده شد — سیگنال معتبر

    # محاسبه ورود، حد ضرر، حد سود
    entry = last_candle['close']
    
    # حد ضرر: زیر آخرین Swing Low (با مارجین 0.3%)
    swing_low = find_swing_low(low, window=5)
    if not swing_low or swing_low >= entry:
        return None
    stop_loss = swing_low * 0.997  # 0.3% زیر سطح

    # حد سود: بر اساس اکستنشن فیبوناچی
    tp1 = fibo_extension(entry, swing_low, 1.618)
    tp2 = fibo_extension(entry, swing_low, 2.618)

    risk = entry - stop_loss
    reward1 = tp1 - entry
    reward2 = tp2 - entry

    return {
        "entry": round(entry, 2),
        "stop_loss": round(stop_loss, 2),
        "take_profit": [round(tp1, 2), round(tp2, 2)],
        "risk_reward": [round(reward1 / risk, 2), round(reward2 / risk, 2)],
        "reason": "Trend + Volume + Pullback + Reversal Pattern"
    }
