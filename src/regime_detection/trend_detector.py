# src/regime_detection/trend_detector.py
import ta

def is_trend_regime(df, adx_threshold=25):
    """
    تشخیص روند با استفاده از ADX
    """
    adx_indicator = ta.trend.ADXIndicator(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=14
    )
    # ✅ استفاده از .loc برای جلوگیری از SettingWithCopyWarning
    df.loc[:, 'adx'] = adx_indicator.adx()
    return df['adx'].iloc[-1] > adx_threshold
