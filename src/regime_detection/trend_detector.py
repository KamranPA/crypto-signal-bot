# src/strategy/trend_detector.py

from src.utils.indicators import calculate_adx
from src.utils.config import get

def is_trending_regime(df):
    if len(df) < 50:
        return False
    adx_threshold = get("regime_detection.adx_threshold", 25)
    adx = calculate_adx(df['high'], df['low'], df['close'], 14).iloc[-1]
    return adx >= adx_threshold
