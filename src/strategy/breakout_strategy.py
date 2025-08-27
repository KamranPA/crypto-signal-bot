# src/strategy/breakout_strategy.py

import pandas as pd
from regime_detection.breakout_detector import is_breakout_regime

def apply_breakout_strategy(df, volume_ratio_threshold=1.8, min_body_ratio=0.6):
    if len(df) < 50:
        return None

    # محاسبه ATR
    tr1 = df['high'] - df['low']
    tr2 = abs(df['high'] - df['close'].shift(1))
    tr3 = abs(df['low'] - df['close'].shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean().iloc[-1]

    if not is_breakout_regime(df, volume_ratio_threshold=volume_ratio_threshold):
        return None

    recent_high = df['high'].rolling(20).max().iloc[-2]
    recent_low = df['low'].rolling(20).min().iloc[-2]
    last = df.iloc[-1]

    # در شکست: SL/TP با تحمل نویز بیشتر
    sl_mult = 1.3
    tp_mult = 2.8

    if last['high'] > recent_high and last['close'] > recent_high:
        entry = last['close']
        sl = recent_high * 0.995
        tp = entry + tp_mult * atr
        if sl >= entry or tp <= entry or sl >= tp:
            return None
        return {
            'signal': 'BUY',
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'regime': 'Breakout Confirmed',
            'risk_reward': tp_mult / sl_mult
        }

    elif last['low'] < recent_low and last['close'] < recent_low:
        entry = last['close']
        sl = recent_low * 1.005
        tp = entry - tp_mult * atr
        if sl <= entry or tp >= entry or sl <= tp:
            return None
        return {
            'signal': 'SELL',
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'regime': 'Breakout Confirmed',
            'risk_reward': tp_mult / sl_mult
        }

    return None
