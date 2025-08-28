# src/regime_detection/breakout_detector.py

def is_breakout_regime(df):
    if len(df) < 20:
        return False
    window = get("regime_detection.breakout_window", 20)
    volume_ratio_threshold = get("regime_detection.breakout_volume_ratio", 1.3)

    recent_high = df['high'].rolling(window).max().iloc[-2]
    recent_low = df['low'].rolling(window).min().iloc[-2]
    current = df.iloc[-1]
    prev = df.iloc[-2]

    confirmed_up = current['high'] > recent_high and current['close'] > prev['close']
    confirmed_down = current['low'] < recent_low and current['close'] < prev['close']

    volume_avg = df['volume'].rolling(window).mean().iloc[-1]
    volume_ratio = current['volume'] / volume_avg

    return (confirmed_up or confirmed_down) and volume_ratio > volume_ratio_threshold
