# src/strategy/range_strategy.py

from src.utils.config import get

def apply_range_strategy(df):
    if len(df) < 20 or not is_range_regime(df):
        return None

    z_threshold = get("strategy.z_score_threshold", 1.5)
    close = df['close']
    mean_price = close.rolling(20).mean().iloc[-1]
    std_price = close.rolling(20).std().iloc[-1]
    z_score = (close.iloc[-1] - mean_price) / std_price

    if abs(z_score) >= z_threshold:
        entry = close.iloc[-1]
        if z_score < -z_threshold:
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
        elif z_score > z_threshold:
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
