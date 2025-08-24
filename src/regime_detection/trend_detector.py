# src/regime_detection/trend_detector.py
"""
این ماژول وظیفه تشخیص روند بازار را بر عهده دارد.
از شاخص ADX برای تشخیص قدرت روند استفاده می‌کند.
"""

import ta


def is_trend_regime(df, adx_threshold=25):
    """
    آیا بازار در روند قوی است؟

    Parameters:
    -----------
    df : pd.DataFrame
        داده‌های OHLCV
    adx_threshold : float
        آستانه ADX برای تشخیص روند (پیش‌فرض 25)

    Returns:
    --------
    bool : True اگر روند قوی باشد، در غیر این صورت False
    """
    # محاسبه ADX
    adx_indicator = ta.trend.ADXIndicator(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=14
    )
    
    # افزودن ADX به DataFrame با استفاده از .loc برای جلوگیری از هشدار
    df.loc[:, 'adx'] = adx_indicator.adx()
    
    # بازگرداندن نتیجه: آیا ADX بالاتر از آستانه است؟
    return df['adx'].iloc[-1] > adx_threshold
