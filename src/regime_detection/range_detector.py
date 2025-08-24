# src/regime_detection/range_detector.py
import pandas as pd

def is_range_regime(df, window=20, threshold=0.7):
    """
    تشخیص بازار رنج با کاهش نوسان و حجم
    """
    price_range = df['high'] - df['low']
    avg_range = price_range.rolling(window).mean()
    current_width = price_range.iloc[-1]

    # ✅ استفاده از .loc
    df.loc[:, 'volatility_ratio'] = current_width / avg_range.iloc[-1]

    # فیلتر حجم
    volume_ratio = df['volume'].iloc[-1] / df['volume'].rolling(window).mean().iloc[-1]

    return (current_width < avg_range.iloc[-1] * threshold) and (volume_ratio < 1.0)
