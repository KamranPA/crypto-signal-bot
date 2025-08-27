import pandas as pd
import numpy as np

def is_range_regime(df, window=20, volatility_threshold=0.7, volume_threshold=0.8):
    """
    تشخیص بازار رنج بر اساس:
    1. کاهش ولتیلیتی نسبی (دامنه قیمت نسبت به قیمت فعلی)
    2. کاهش حجم معاملات نسبت به میانگین
    3. عدم وجود روند مشخص (با استفاده از ADX تقریبی بدون کتابخانه)

    ورودی:
        df: دیتافریم با ستون‌های 'high', 'low', 'close', 'volume'
        window: پنجره زمانی برای محاسبات (پیش‌فرض 20 دوره)
        volatility_threshold: آستانه ولتیلیتی (مثلاً 70% از میانگین تاریخی)
        volume_threshold: آستانه حجم (مثلاً 80% از میانگین حجم)

    خروجی:
        bool: آیا بازار در حالت رنج است؟
    """
    if len(df) < window + 1:
        return False  # داده کافی نیست

    df = df.copy()
    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']

    # 1. ولتیلیتی نسبی (دامنه درصدی)
    true_range = high - low  # در داده‌های روزانه ساده، TR ≈ high - low
    true_range_pct = true_range / close
    avg_true_range_pct = true_range_pct.rolling(window, min_periods=1).mean()
    current_volatility_pct = true_range_pct.iloc[-1]
    avg_volatility_pct = avg_true_range_pct.iloc[-1]

    in_low_volatility = current_volatility_pct < avg_volatility_pct * volatility_threshold

    # 2. حجم نسبی
    avg_volume = volume.rolling(window, min_periods=1).mean()
    current_volume_ratio = volume.iloc[-1] / avg_volume.iloc[-1]
    in_low_volume = current_volume_ratio < volume_threshold

    # 3. تشخیص عدم روند (تقریب ADX بدون کتابخانه)
    # محاسبه تغییر قیمت متوسط (برای تخمین جهت‌داری)
    price_change = np.abs(close.diff(periods=1))
    total_change = price_change.rolling(window, min_periods=1).sum()

    # تغییر جهتی (Directional Movement تقریبی)
    up_move = (high - high.shift(1))
    down_move = (low.shift(1) - low)
    pos_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    neg_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

    # میانگین متحرک ساده برای DM (با exponential smoothing ساده‌شده)
    alpha = 2 / (window + 1)
    smoothed_pos_dm = pd.Series(pos_dm).ewm(alpha=alpha, min_periods=1).mean().iloc[-1]
    smoothed_neg_dm = pd.Series(neg_dm).ewm(alpha=alpha, min_periods=1).mean().iloc[-1]
    tr_smoothed = true_range.ewm(alpha=alpha, min_periods=1).mean().iloc[-1]

    if tr_smoothed == 0:
        di_diff = 0
    else:
        di_plus = (smoothed_pos_dm / tr_smoothed) * 100
        di_minus = (smoothed_neg_dm / tr_smoothed) * 100
        di_diff = abs(di_plus - di_minus)

    # اگر تفاوت DI کم باشد، یعنی روند ضعیف است (نشانه رنج)
    in_no_trend = di_diff < 10  # مقدار 10 یک آستانه تجربی است

    # ترکیب تمام شرایط
    return in_low_volatility and in_low_volume and in_no_trend
