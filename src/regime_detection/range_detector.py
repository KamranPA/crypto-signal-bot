# src/regime_detection/range_detector.py

from src.utils.indicators import calculate_atr
from src.utils.config import get

def is_range_regime(df):
    if len(df) < 50:
        return False

    volatility_threshold = get("regime_detection.range_volatility_threshold", 0.03)
    volume_threshold = get("regime_detection.range_volume_threshold", 0.8)

    # محاسبه ولتیلیتی نسبی
    atr = calculate_atr(df['high'], df['low'], df['close'], 14).iloc[-1]
    price_level = df['close'].mean()
    volatility_pct = atr / price_level

    # حجم نسبی
    volume_avg = df['volume'].rolling(20).mean().iloc[-1]
    volume_ratio = df['volume'].iloc[-1] / volume_avg

    return volatility_pct < volatility_threshold and volume_ratio < volume_threshold
