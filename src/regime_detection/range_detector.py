# src/regime_detection/range_detector.py
"""
تشخیص بازار رنج با کاهش نوسان و حجم
"""
def is_range_regime(df, window=20, threshold=0.7):
    """
    آیا بازار در حالت رنج است؟
    """
    price_range = df['high'] - df['low']
    avg_range = price_range.rolling(window).mean()
    current_width = price_range.iloc[-1]

    # فیلتر حجم: در رنج، حجم کم است
    volume_ratio = df['volume'].iloc[-1] / df['volume'].rolling(window).mean().iloc[-1]

    in_low_volatility = current_width < avg_range.iloc[-1] * threshold
    in_low_volume = volume_ratio < 1.0

    return in_low_volatility and in_low_volume
