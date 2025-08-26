# src/strategy/trend_strategy.py
import ta

def apply_trend_strategy(df, adx_threshold=25, volume_ratio_threshold=1.2):
    """
    استراتژی روند: فقط در روند قوی و با حجم مناسب
    """
    if len(df) < 50:
        return None

    # محاسبه EMA 21
    ema_21 = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()

    # محاسبه ADX
    adx_indicator = ta.trend.ADXIndicator(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=14
    )
    adx = adx_indicator.adx()
    adx_value = adx.iloc[-1]

    # محاسبه ATR
    atr = ta.volatility.AverageTrueRange(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=14
    ).average_true_range()

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # فیلتر حجم
    volume_avg = df['volume'].rolling(20).mean().iloc[-1]
    volume_ratio = last['volume'] / volume_avg

    # 🔹 فقط اگر روند قوی باشد
    if adx_value > adx_threshold and volume_ratio > volume_ratio_threshold:
        if last['close'] > ema_21.iloc[-1] and prev['close'] <= ema_21.iloc[-2]:
            entry = last['close']
            sl = min(prev['low'], entry - 1.5 * atr.iloc[-1])
            tp = entry + 2.5 * atr.iloc[-1]

            if sl >= entry or tp <= entry or sl >= tp:
                return None

            return {
                'signal': 'BUY',
                'entry': entry,
                'stop_loss': sl,
                'take_profit': tp,
                'regime': 'Strong Trend_Up'
            }
        elif last['close'] < ema_21.iloc[-1] and prev['close'] >= ema_21.iloc[-2]:
            entry = last['close']
            sl = max(prev['high'], entry + 1.5 * atr.iloc[-1])
            tp = entry - 2.5 * atr.iloc[-1]

            if sl <= entry or tp >= entry or sl <= tp:
                return None

            return {
                'signal': 'SELL',
                'entry': entry,
                'stop_loss': sl,
                'take_profit': tp,
                'regime': 'Strong Trend_Down'
            }

    return None
