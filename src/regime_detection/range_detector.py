# src/regime_detection/range_detector.py
"""
تشخیص رژیم رنج با استفاده از پهنای نوسان (Volatility Width) و حجم
"""
import pandas as pd

def is_range_regime(df, window=20, threshold=0.7):
    """
    آیا بازار در حالت رنج (ناحسم) است؟
    - بر اساس کاهش نوسان (کوچک بودن محدوده کندل‌ها)
    - بر اساس حجم پایین
    """
    # پهنای نوسان (میانگین دامنه کندل‌ها)
    price_range = df['high'] - df['low']
    avg_range = price_range.rolling(window).mean()
    current_width = price_range.iloc[-1]

    # نسبت نوسان فعلی به میانگین
    width_ratio = current_width / avg_range.iloc[-1]

    # فیلتر حجم: حجم کم = نشانه رنج
    volume_avg = df['volume'].rolling(window).mean()
    volume_ratio = df['volume'].iloc[-1] / volume_avg.iloc[-1]

    # شرط: نوسان کم و حجم کم
    in_low_volatility = width_ratio < threshold
    in_low_volume = volume_ratio < 1.0

    return in_low_volatility and in_low_volume
