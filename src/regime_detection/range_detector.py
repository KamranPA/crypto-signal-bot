# src/regime_detection/range_detector.py
def is_range_regime(df, window=20, threshold=0.7):
    price_range = df['high'] - df['low']
    avg_range = price_range.rolling(window).mean()
    current_width = price_range.iloc[-1]
    return current_width < avg_range.iloc[-1] * threshold
