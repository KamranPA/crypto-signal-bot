# src/strategy/range_strategy.py
import ta

def apply_range_strategy(df, adx_threshold=20):
    """
    استراتژی رنج: فقط اگر ADX < 20 باشد و قیمت در حمایت/مقاومت باشد
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

    # 🔹 فقط اگر بازار واقعاً رنج باشد
    if adx_value >= adx_threshold:
        return None  # ❌ روند یا شکست، نه رنج

    last = df.iloc[-1]
    lower_band = df['low'].rolling(20).min().iloc[-1]
    upper_band = df['high'].rolling(20).max().iloc[-1]

    # محاسبه ATR برای SL/TP
    atr = ta.volatility.AverageTrueRange(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=14
    ).average_true_range()

    # سیگنال خرید در پایین کانال
    if abs(last['close'] - lower_band) / lower_band < 0.005:
        entry = last['close']
        sl = lower_band * 0.99
        tp = (lower_band + upper_band) / 2

        # ✅ بررسی منطقی بودن SL و TP
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
        tp = (lower_band + upper_band) / 2

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
