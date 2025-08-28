# src/strategy/trend_strategy.py

import pandas as pd

def is_range_regime(df):
    """
    تشخیص بازار رنج: ولتیلیتی و حجم پایین
    """
    if len(df) < 50:
        return False
    
    # محاسبه ATR (شبیه به ولتیلیتی)
    high = df['high']
    low = df['low']
    close = df['close']
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean().iloc[-1]
    
    # نسبت ولتیلیتی به قیمت
    price_level = df['close'].mean()
    volatility_pct = atr / price_level

    # حجم نسبی
    volume_avg = df['volume'].rolling(20).mean().iloc[-1]
    volume_ratio = df['volume'].iloc[-1] / volume_avg

    # شرط رنج: ولتیلیتی کم + حجم کم
    return volatility_pct < 0.03 and volume_ratio < 0.8


def apply_trend_strategy(df):
    """
    استراتژی روند: فقط در بازارهای غیررنج و با عبور از EMA
    """
    if len(df) < 50:
        return None

    # اگر بازار رنج بود، سیگنال نده
    if is_range_regime(df):
        return None

    # محاسبه EMA 21
    ema_21 = df['close'].ewm(span=21, adjust=False).mean()

    # محاسبه ATR برای حد ضرر و سود
    tr1 = df['high'] - df['low']
    tr2 = abs(df['high'] - df['close'].shift(1))
    tr3 = abs(df['low'] - df['close'].shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean().iloc[-1]

    # آخرین و قبلی
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # فیلتر حجم: حجم بالاتر از میانگین 20 روز اخیر
    volume_avg = df['volume'].rolling(20).mean().iloc[-1]
    volume_ratio = last['volume'] / volume_avg
    if volume_ratio < 1.2:
        return None

    # BUY: عبور قیمت از EMA به سمت بالا
    if last['close'] > ema_21.iloc[-1] and prev['close'] <= ema_21.iloc[-2]:
        entry = last['close']
        sl = entry - 1.5 * atr
        tp = entry + 2.5 * atr
        if sl >= entry or tp <= entry:
            return None
        return {
            'signal': 'BUY',
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'regime': 'Strong Trend_Up'
        }

    # SELL: عبور قیمت از EMA به سمت پایین
    elif last['close'] < ema_21.iloc[-1] and prev['close'] >= ema_21.iloc[-2]:
        entry = last['close']
        sl = entry + 1.5 * atr
        tp = entry - 2.5 * atr
        if sl <= entry or tp >= entry:
            return None
        return {
            'signal': 'SELL',
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'regime': 'Strong Trend_Down'
        }

    return None
