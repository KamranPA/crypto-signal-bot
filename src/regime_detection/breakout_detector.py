# src/regime_detection/breakout_detector.py
def is_breakout_regime(df, window=20):
    """
    آیا شکست واقعی رخ داده؟
    """
    recent_high = df['high'].rolling(window).max().iloc[-2]
    recent_low = df['low'].rolling(window).min().iloc[-2]
    current = df.iloc[-1]
    prev = df.iloc[-2]

    confirmed_up = current['high'] > recent_high and current['close'] > prev['close']
    confirmed_down = current['low'] < recent_low and current['close'] < prev['close']

    volume_ratio = current['volume'] / df['volume'].rolling(window).mean().iloc[-1]

    return (confirmed_up or confirmed_down) and (volume_ratio > 1.3)
