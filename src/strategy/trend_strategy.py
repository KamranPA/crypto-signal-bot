# src/strategy/trend_strategy.py

import pandas as pd

def is_range_regime(df):
    if len(df) < 50:
        return False
    tr1 = df['high'] - df['low']
    tr2 = abs(df['high'] - df['close'].shift(1))
    tr3 = abs(df['low'] - df['close'].shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean().iloc[-1]
    volatility_pct = atr / df['close'].mean()
    volume_ratio = df['volume'].iloc[-1] / df['volume'].rolling(20).mean().iloc[-1]
    return volatility_pct < 0.03 and volume_ratio < 0.8


def apply_trend_strategy(df):
    if len(df) < 50 or is_range_regime(df):
        return None

    ema_21 = df['close'].ewm(span=21, adjust=False).mean()
    atr = (df['high'] - df['low']).rolling(14).mean().iloc[-1]
    volume_avg = df['volume'].rolling(20).mean().iloc[-1]
    volume_ratio = df['volume'].iloc[-1] / volume_avg

    if volume_ratio < 1.2:
        return None

    if df['close'].iloc[-1] > ema_21.iloc[-1] and df['close'].iloc[-2] <= ema_21.iloc[-2]:
        entry = df['close'].iloc[-1]
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
    elif df['close'].iloc[-1] < ema_21.iloc[-1] and df['close'].iloc[-2] >= ema_21.iloc[-2]:
        entry = df['close'].iloc[-1]
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
