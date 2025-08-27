# src/regime_detection/range_detector.py

import pandas as pd
import numpy as np

def is_range_regime(df, window=20, volatility_threshold=0.7, volume_threshold=0.8):
    """
    تشخیص بازار رنج با استفاده از:
    - ولتیلیتی نسبی (درصدی)
    - حجم نسبی
    - عدم وجود روند (تقریب ADX)
    
    ورودی:
        df: DataFrame با ستون‌های 'high', 'low', 'close', 'volume'
        window: پنجره زمانی برای محاسبات
        volatility_threshold: آستانه ولتیلیتی (مثلاً 70% از میانگین)
        volume_threshold: آستانه حجم (مثلاً 80% از میانگین)
    """
    if len(df) < window + 1:
        return False

    # 1. ولتیلیتی نسبی (High - Low) / Close
    true_range = df['high'] - df['low']
    true_range_pct = true_range / df['close']
    avg_true_range_pct = true_range_pct.rolling(window).mean()
    current_volatility_pct = true_range_pct.iloc[-1]
    in_low_volatility = current_volatility_pct < avg_true_range_pct.iloc[-1] * volatility_threshold

    # 2. حجم نسبی
    avg_volume = df['volume'].rolling(window).mean()
    volume_ratio = df['volume'].iloc[-1] / avg_volume.iloc[-1]
    in_low_volume = volume_ratio < volume_threshold

    # 3. تشخیص روند (تقریب ADX)
    high = df['high']
    low = df['low']
    close = df['close']

    # True Range
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Directional Movement
    up_move = high.diff()
    down_move = low.diff()
    pos_dm = ((up_move > down_move) & (up_move > 0)) * up_move
    neg_dm = ((down_move > up_move) & (down_move > 0)) * down_move

    # EMA-like smoothing (Wilder's method تقریبی)
    alpha = 2 / (window + 1)
    smoothed_pos_dm = pos_dm.ewm(alpha=alpha, min_periods=1).mean()
    smoothed_neg_dm = neg_dm.ewm(alpha=alpha, min_periods=1).mean()
    atr = tr.ewm(alpha=alpha, min_periods=1).mean()

    # DI+
    di_plus = (smoothed_pos_dm / atr) * 100
    di_minus = (smoothed_neg_dm / atr) * 100

    # DX and ADX (تقریبی)
    dx = abs(di_plus - di_minus) / (di_plus + di_minus + 1e-8) * 100
    adx = dx.ewm(alpha=alpha, min_periods=1).mean()

    in_no_trend = adx.iloc[-1] < 20  # اگر ADX < 20، روند ضعیف است

    # ترکیب شرایط
    return in_low_volatility and in_low_volume and in_no_trend
