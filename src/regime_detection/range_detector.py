# src/regime_detection/range_detector.py

def is_range_regime(df, volatility_threshold=0.03, volume_ratio_threshold=0.8):
    """
    تشخیص رژیم رنج بر اساس ولتیلیتی و حجم
    """
    if len(df) < 50:
        return False

    # محاسبه ATR
    tr1 = df['high'] - df['low']
    tr2 = abs(df['high'] - df['close'].shift(1))
    tr3 = abs(df['low'] - df['close'].shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean().iloc[-1]

    # نسبت ولتیلیتی به قیمت
    price_level = df['close'].rolling(50).mean().iloc[-1]
    volatility_pct = atr / price_level

    # محاسبه حجم
    volume_avg = df['volume'].rolling(20).mean().iloc[-1]
    volume_ratio = df['volume'].iloc[-1] / volume_avg

    # شرط رنج: ولتیلیتی پایین + حجم پایین
    in_low_volatility = volatility_pct < volatility_threshold
    in_low_volume = volume_ratio < volume_ratio_threshold

    return in_low_volatility and in_low_volume
