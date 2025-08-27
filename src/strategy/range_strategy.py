# src/strategy/range_strategy.py

import pandas as pd
from regime_detection.range_detector import is_range_regime

def apply_range_strategy(df, window=20):
    if len(df) < window + 1:
        return None

    if not is_range_regime(df):
        return None

    close = df['close']
    mean_price = close.rolling(window).mean().iloc[-1]
    std_price = close.rolling(window).std().iloc[-1]
    z_score = (close.iloc[-1] - mean_price) / std_price

    if abs(z_score) < 1.5:
        return None

    # محاسبه ATR
    tr1 = df['high'] - df['low']
    tr2 = abs(df['high'] - df['close'].shift(1))
    tr3 = abs(df['low'] - df['close'].shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean().iloc[-1]

    # در رنج: SL/TP تنگ‌تر
    sl_mult = 0.5
    tp_mult = 1.5

    if z_score < -1.5:
        entry = close.iloc[-1]
        sl = entry - sl_mult * atr
        tp = mean_price
        if sl >= entry or tp <= entry:
            return None
        return {
            'signal': 'BUY',
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'regime': 'Range_Mean_Reversion',
            'risk_reward': (tp - entry) / (entry - sl)
        }
    elif z_score > 1.5:
        entry = close.iloc[-1]
        sl = entry + sl_mult * atr
        tp = mean_price
        if sl <= entry or tp >= entry:
            return None
        return {
            'signal': 'SELL',
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'regime': 'Range_Mean_Reversion',
            'risk_reward': (entry - tp) / (sl - entry)
        }
    return None
