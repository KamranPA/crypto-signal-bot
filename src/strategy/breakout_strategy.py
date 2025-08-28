# src/strategy/breakout_strategy.py

import pandas as pd

def apply_breakout_strategy(df, volume_ratio_threshold=1.8, min_body_ratio=0.6):
    """
    استراتژی شکست: فقط در شرایط شکست
    """
    if len(df) < 50:
        return None

    # محاسبه حجم
    volume_avg = df['volume'].rolling(20).mean().iloc[-1]
    volume_ratio = df['volume'].iloc[-1] / volume_avg

    if volume_ratio < volume_ratio_threshold:
        return None

    # بررسی بدن کندل
    body_size = abs(df['close'].iloc[-1] - df['open'].iloc[-1])
    atr = (df['high'] - df['low']).rolling(14).mean().iloc[-1]

    if body_size < min_body_ratio * atr:
        return None

    # شرط شکست بالا
    recent_high = df['high'].rolling(20).max().iloc[-2]
    if df['high'].iloc[-1] > recent_high and df['close'].iloc[-1] > recent_high:
        entry = df['close'].iloc[-1]
        sl = recent_high * 0.995
        tp = entry + 2.5 * atr
        if sl >= entry or tp <= entry or sl >= tp:
            return None
        return {
            'signal': 'BUY',
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'regime': 'Breakout Confirmed'
        }

    # شرط شکست پایین
    recent_low = df['low'].rolling(20).min().iloc[-2]
    if df['low'].iloc[-1] < recent_low and df['close'].iloc[-1] < recent_low:
        entry = df['close'].iloc[-1]
        sl = recent_low * 1.005
        tp = entry - 2.5 * atr
        if sl <= entry or tp >= entry or sl <= tp:
            return None
        return {
            'signal': 'SELL',
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'regime': 'Breakout Confirmed'
        }

    return None
