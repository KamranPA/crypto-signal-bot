# src/regime_detection/range_detector.py
import ta

def is_range_regime(df, window=20, threshold=0.7):
    bb_width = df['high'] - df['low']
    avg_width = bb_width.rolling(window).mean()
    return (bb_width < avg_width * threshold).iloc[-1]
