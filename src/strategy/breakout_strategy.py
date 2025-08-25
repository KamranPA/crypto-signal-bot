# src/strategy/breakout_strategy.py
import ta

def apply_breakout_strategy(df, volume_ratio_threshold=1.8, min_body_ratio=0.6):
    """
    استراتژی شکست: فقط با حجم بالا و تأیید کندل
    """
    if len(df) < 50:
        return None

    # محاسبه ATR
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
    adx_slope = adx.iloc[-1] - adx.iloc[-2]

    last = df.iloc[-1]
    prev = df.iloc[-2]
    volume_avg = df['volume'].rolling(20).mean().iloc[-1]
    volume_ratio = last['volume'] / volume_avg
    body_size = abs(last['close'] - last['open'])

    recent_high = df['high'].rolling(20).max().iloc[-2]
    recent_low = df['low'].rolling(20).min().iloc[-2]

    # شرط: شکست با حجم بالا و بدنه قوی
    if (adx_slope > 0 and 
        volume_ratio > volume_ratio_threshold and 
        body_size > min_body_ratio * atr.iloc[-1]):

        if last['high'] > recent_high and last['close'] > recent_high:
            return {
                'signal': 'BUY',
                'entry': last['close'],
                'stop_loss': recent_high * 0.99,
                'take_profit': last['close'] + 2.5 * atr.iloc[-1],
                'regime': 'Breakout Confirmed'
            }
        elif last['low'] < recent_low and last['close'] < recent_low:
            return {
                'signal': 'SELL',
                'entry': last['close'],
                'stop_loss': recent_low * 1.01,
                'take_profit': last['close'] - 2.5 * atr.iloc[-1],
                'regime': 'Breakout Confirmed'
            }
    return None
