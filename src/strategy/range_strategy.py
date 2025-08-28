# src/strategy/range_strategy.py

import pandas as pd
from regime_detection.range_detector import is_range_regime

def apply_range_strategy(df, window=20):
    """
    استراتژی رنج: فقط در بازارهای رنج
    """
    if len(df) < window + 1:
        return None

    if not is_range_regime(df):
        return None

    close = df['close']
    mean_price = close.rolling(window).mean().iloc[-1]
    std_price = close.rolling(window).std().iloc[-1]
    z_score = (close.iloc[-1] - mean_price) / std_price

    if abs(z_score) >= 1.5:
        entry = close.iloc[-1]
        if z_score < -1.5:
            sl = entry - 0.5 * std_price
            tp = mean_price
            if sl >= entry or tp <= entry:
                return None
            return {
                'signal': 'BUY',
                'entry': entry,
                'stop_loss': sl,
                'take_profit': tp,
                'regime': 'Range_Mean_Reversion'
            }
        elif z_score > 1.5:
            sl = entry + 0.5 * std_price
            tp = mean_price
            if sl <= entry or tp >= entry:
                return None
            return {
                'signal': 'SELL',
                'entry': entry,
                'stop_loss': sl,
                'take_profit': tp,
                'regime': 'Range_Mean_Reversion'
            }

    return None
