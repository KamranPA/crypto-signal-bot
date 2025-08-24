# src/regime_detection/trend_detector.py
import ta

def is_trend_regime(df, adx_threshold=25):
    """
    آیا بازار در روند است؟ (بدون مسدود کردن، فقط تشخیص)
    """
    adx_indicator = ta.trend.ADXIndicator(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=14
    )
    df.loc[:, 'adx'] = adx_indicator.adx()
    return df['adx'].iloc[-1] > adx_threshold
