def is_trend_regime(df, adx_threshold=25, ema_slope_window=5):
    adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14)
    df['adx'] = adx.adx()
    
    # فیلتر اضافه: شیب EMA باید مثبت/منفی باشد
    df['ema_21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
    slope = (df['ema_21'] - df['ema_21'].shift(ema_slope_window)) / ema_slope_window
    
    return (df['adx'].iloc[-1] > adx_threshold) and (abs(slope.iloc[-1]) > 0)
