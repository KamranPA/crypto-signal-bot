# src/strategy/range_strategy.py
import ta

def apply_range_strategy(df, adx_threshold=20):
    """
    استراتژی رنج: خرید در پایین و فروش در بالای کانال
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

    last = df.iloc[-1]
    lower_band = df['low'].rolling(20).min().iloc[-1]
    upper_band = df['high'].rolling(20).max().iloc[-1]

    # شرط: رنج واقعی (ADX پایین)
    if adx.iloc[-1] < adx_threshold:
        if abs(last['close'] - lower_band) / lower_band < 0.005:
            return {
                'signal': 'BUY',
                'entry': last['close'],
                'stop_loss': lower_band * 0.99,
                'take_profit': (lower_band + upper_band) / 2,
                'regime': 'Range'
            }
        elif abs(last['close'] - upper_band) / upper_band < 0.005:
            return {
                'signal': 'SELL',
                'entry': last['close'],
                'stop_loss': upper_band * 1.01,
                'take_profit': (lower_band + upper_band) / 2,
                'regime': 'Range'
            }
    return None
