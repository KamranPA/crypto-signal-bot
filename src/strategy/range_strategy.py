# src/strategy/range_strategy.py
import ta

def apply_range_strategy(df, adx_threshold=20, risk_reward_ratio=1.5):
    """
    استراتژی رنج با نسبت ریسک به پاداش منطقی
    """
    if len(df) < 50:
        return None

    # محاسبه ADX
    adx_indicator = ta.trend.ADXIndicator(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=14
    )
    adx = adx_indicator.adx()
    adx_value = adx.iloc[-1]

    # فقط اگر بازار واقعاً رنج باشد
    if adx_value >= adx_threshold:
        return None

    # محاسبه ATR
    atr = ta.volatility.AverageTrueRange(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=14
    ).average_true_range()

    last = df.iloc[-1]
    lower_band = df['low'].rolling(20).min().iloc[-1]
    upper_band = df['high'].rolling(20).max().iloc[-1]

    # ✅ فاصله ورود به SL بر اساس ATR
    max_sl_distance = 2.0 * atr.iloc[-1]  # حداکثر فاصله SL از ورود

    # سیگنال خرید در پایین کانال
    if abs(last['close'] - lower_band) / lower_band < 0.005:
        entry = last['close']
        sl = lower_band * 0.99

        # ✅ اگر SL خیلی دور بود، آن را محدود کن
        if (entry - sl) > max_sl_distance:
            sl = entry - max_sl_distance

        # ✅ TP = SL × نسبت R:R
        tp = entry + (entry - sl) * risk_reward_ratio

        if sl >= entry or tp <= entry or sl >= tp:
            return None

        return {
            'signal': 'BUY',
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'regime': 'Range'
        }

    # سیگنال فروش در بالای کانال
    elif abs(last['close'] - upper_band) / upper_band < 0.005:
        entry = last['close']
        sl = upper_band * 1.01

        if (sl - entry) > max_sl_distance:
            sl = entry + max_sl_distance

        tp = entry - (sl - entry) * risk_reward_ratio

        if sl <= entry or tp >= entry or sl <= tp:
            return None

        return {
            'signal': 'SELL',
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'regime': 'Range'
        }

    return None
