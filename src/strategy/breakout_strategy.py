# src/strategy/breakout_strategy.py

from regime_detection.breakout_detector import is_breakout_regime

def apply_breakout_strategy(df, volume_ratio_threshold=1.8, min_body_ratio=0.6):
    if len(df) < 50:
        return None

    tr1 = df['high'] - df['low']
    tr2 = abs(df['high'] - df['close'].shift(1))
    tr3 = abs(df['low'] - df['close'].shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean().iloc[-1]

    last = df.iloc[-1]
    body_size = abs(last['close'] - last['open'])

    if not is_breakout_regime(df, window=20, volume_ratio_threshold=volume_ratio_threshold):
        return None

    if body_size < min_body_ratio * atr:
        return None

    recent_high = df['high'].rolling(20).max().iloc[-2]
    recent_low = df['low'].rolling(20).min().iloc[-2]

    if last['high'] > recent_high and last['close'] > recent_high:
        entry = last['close']
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

    elif last['low'] < recent_low and last['close'] < recent_low:
        entry = last['close']
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
