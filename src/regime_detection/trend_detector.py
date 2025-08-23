# src/regime_detection/trend_detector.py
"""
تشخیص رژیم روند با استفاده از ADX و شیب EMA
"""
import ta

def is_trend_regime(df, adx_threshold=25):
    """
    آیا بازار در روند قوی است؟
    """
    # محاسبه ADX
    adx_indicator = ta.trend.ADXIndicator(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=14
    )
    df['adx'] = adx_indicator.adx()

    # فقط اگر ADX بالای آستانه باشد، روند قوی است
    return df['adx'].iloc[-1] > adx_threshold
