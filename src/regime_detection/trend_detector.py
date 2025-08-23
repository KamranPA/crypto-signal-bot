# src/regime_detection/trend_detector.py
import ta  # ← این خط حتماً باید وجود داشته باشد

def is_trend_regime(df, adx_threshold=25):
    adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14)
    df['adx'] = adx.adx()
    return df['adx'].iloc[-1] > adx_threshold
