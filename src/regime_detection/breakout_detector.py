# src/regime_detection/breakout_detector.py
def is_breakout_regime(df, window=20):
    recent_high = df['high'].rolling(window).max().iloc[-2]
    recent_low = df['low'].rolling(window).min().iloc[-2]
    current_high = df['high'].iloc[-1]
    current_low = df['low'].iloc[-1]
    return current_high > recent_high or current_low < recent_low
