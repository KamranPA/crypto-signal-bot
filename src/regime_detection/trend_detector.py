# src/regime_detection/trend_detector.py
import ta

def is_trend_regime(df, adx_threshold=25):
    """
    تشخیص روند با ADX
    """
    # محاسبه ADX
    adx_indicator = ta.trend.ADXIndicator(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=14
    )
    
    # ⚠️ اشتباه: df['adx'] = adx_indicator.adx() → ممکن ایجاد warning
    # ✅ صحیح: استفاده از .loc
    df.loc[:, 'adx'] = adx_indicator.adx()
    
    return df['adx'].iloc[-1] > adx_threshold
