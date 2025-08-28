# src/strategy/breakout_strategy.py

from src.utils.config import get
from src.utils.indicators import calculate_atr

def apply_breakout_strategy(df):
    if len(df) < 20:
        return None

    volume_ratio_threshold = get("regime_detection.breakout_volume_ratio", 1.3)
    min_body_ratio = 0.6
    window = 20

    volume_avg = df['volume'].rolling(window).mean().iloc[-1]
    volume_ratio = df['volume'].iloc[-1] / volume_avg

    if volume_ratio < volume_ratio_threshold:
        return None

    body_size = abs(df['close'].iloc[-1] - df['open'].iloc[-1])
    atr = calculate_atr(df['high'], df['low'], df['close'], 14).iloc[-1]

    if body_size < min_body_ratio * atr:
        return None

    recent_high = df['high'].rolling(window).max().iloc[-2]
    recent_low = df['low'].rolling(window).min().iloc[-2]

    if df['high'].iloc[-1] > recent_high and df['close'].iloc[-1] > recent_high:
        entry = df['close'].iloc[-1]
        sl = recent_high * 0.995
        tp = entry + 2.5 * atr
        if sl >= entry or tp <= entry:
            return None
        return {
            'signal': 'BUY',
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'regime': 'Breakout Confirmed'
        }

    if df['low'].iloc[-1] < recent_low and df['close'].iloc[-1] < recent_low:
        entry = df['close'].iloc[-1]
        sl = recent_low * 1.005
        tp = entry - 2.5 * atr
        if sl <= entry or tp >= entry:
            return None
        return {
            'signal': 'SELL',
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'regime': 'Breakout Confirmed'
        }

    return None
