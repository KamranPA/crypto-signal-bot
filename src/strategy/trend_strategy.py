# src/strategy/trend_strategy.py

from src.utils.indicators import calculate_adx, calculate_atr
from src.utils.config import get
from src.regime_detection import is_range_regime

def apply_trend_strategy(df):
    if len(df) < 50 or is_range_regime(df):
        return None

    adx = calculate_adx(df['high'], df['low'], df['close'], 14).iloc[-1]
    adx_threshold = get("regime_detection.adx_threshold", 25)
    volume_avg = df['volume'].rolling(20).mean().iloc[-1]
    volume_ratio = df['volume'].iloc[-1] / volume_avg

    if adx < adx_threshold or volume_ratio < 1.2:
        return None

    ema_21 = df['close'].ewm(span=21, adjust=False).mean()
    atr = calculate_atr(df['high'], df['low'], df['close'], 14).iloc[-1]

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
