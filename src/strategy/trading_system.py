# src/strategy/trend_strategy.py
import ta

def apply_trend_strategy(df, adx_threshold=25, volume_ratio_threshold=1.2):
    """
    استراتژی روند: فقط در روند قوی و با حجم مناسب
    """
    if len(df) < 50:
        return None

    # محاسبه شاخص‌ها
    ema_21 = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
    atr = ta.volatility.AverageTrueRange(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=14
    ).average_true_range()

    # محاسبه ADX
    adx_indicator = ta.trend.ADXIndicator(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=14
    )
    adx = adx_indicator.adx()

    last = df.iloc[-1]
    prev = df.iloc[-2]
    volume_avg = df['volume'].rolling(20).mean().iloc[-1]
    volume_ratio = last['volume'] / volume_avg

    # شرط: روند قوی و حجم کافی
    if adx.iloc[-1] > adx_threshold and volume_ratio > volume_ratio_threshold:
        if last['close'] > ema_21.iloc[-1] and prev['close'] <= ema_21.iloc[-2]:
            return {
                'signal': 'BUY',
                'entry': last['close'],
                'stop_loss': min(prev['low'], last['close'] - 1.5 * atr.iloc[-1]),
                'take_profit': last['close'] + 2.5 * atr.iloc[-1],
                'regime': 'Strong Trend_Up'
            }
        elif last['close'] < ema_21.iloc[-1] and prev['close'] >= ema_21.iloc[-2]:
            return {
                'signal': 'SELL',
                'entry': last['close'],
                'stop_loss': max(prev['high'], last['close'] + 1.5 * atr.iloc[-1]),
                'take_profit': last['close'] - 2.5 * atr.iloc[-1],
                'regime': 'Strong Trend_Down'
            }
    return None
