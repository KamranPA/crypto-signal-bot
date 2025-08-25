# src/strategy/trading_system.py
"""
سیستم تولید سیگنال بر اساس تشخیص رژیم بازار: روند، رنج، شکست
"""
from src.regime_detection.range_detector import is_range_regime
from src.regime_detection.trend_detector import is_trend_regime
from src.regime_detection.breakout_detector import is_breakout_regime
import ta


def generate_signal(df):
    """
    تولید سیگنال بر اساس رژیم بازار
    """
    if len(df) < 50:
        return None

    # محاسبه EMA 21
    df['ema_21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()

    # محاسبه ATR
    df['atr'] = ta.volatility.AverageTrueRange(
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
    df.loc[:, 'adx'] = adx_indicator.adx()
    adx_value = df['adx'].iloc[-1]

    # آخرین و کندل قبلی
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # فیلتر حجم
    volume_avg = df['volume'].rolling(20).mean().iloc[-1]
    volume_ratio = last['volume'] / volume_avg

    # تشخیص رژیم
    in_trend = is_trend_regime(df)
    in_range = is_range_regime(df)
    in_breakout = is_breakout_regime(df)

    # متغیرهای سیگنال
    signal = entry = sl = tp = None
    regime = 'Uncertain'

    # 1. روند قوی (فقط اگر ADX > 25 و حجم بالا باشد)
    if in_trend and adx_value > 25:
        if volume_ratio > 1.2:  # فقط با حجم بالا
            # سیگنال خرید
            if last['close'] > last['ema_21'] and prev['close'] <= prev['ema_21']:
                signal = 'BUY'
                entry = last['close']
                sl = min(prev['low'], entry - 1.5 * df['atr'].iloc[-1])
                tp = entry + 2.5 * df['atr'].iloc[-1]
                regime = 'Strong Trend_Up'

            # سیگنال فروش
            elif last['close'] < last['ema_21'] and prev['close'] >= prev['ema_21']:
                signal = 'SELL'
                entry = last['close']
                sl = max(prev['high'], entry + 1.5 * df['atr'].iloc[-1])
                tp = entry - 2.5 * df['atr'].iloc[-1]
                regime = 'Strong Trend_Down'

    # 2. رنج (فقط اگر ADX < 20 باشد)
    elif in_range and adx_value < 20:
        regime = 'Range'
        lower_band = df['low'].rolling(20).min().iloc[-1]
        upper_band = df['high'].rolling(20).max().iloc[-1]

        # سیگنال خرید در پایین کانال
        if abs(last['close'] - lower_band) / lower_band < 0.005:
            signal = 'BUY'
            entry = last['close']
            sl = lower_band * 0.99
            tp = (lower_band + upper_band) / 2

        # سیگنال فروش در بالای کانال
        elif abs(last['close'] - upper_band) / upper_band < 0.005:
            signal = 'SELL'
            entry = last['close']
            sl = upper_band * 1.01
            tp = (lower_band + upper_band) / 2

    # 3. شکست (با تأیید حجم و افزایش ADX)
    elif in_breakout:
        adx_slope = adx_value - df['adx'].iloc[-2]
        if adx_slope > 0 and volume_ratio > 1.3:  # تأیید با حجم و روند جدید
            recent_high = df['high'].rolling(20).max().iloc[-2]
            recent_low = df['low'].rolling(20).min().iloc[-2]

            if last['high'] > recent_high:
                signal = 'BUY'
                entry = last['close']
                sl = recent_high * 0.99
                tp = entry + 3.0 * df['atr'].iloc[-1]
                regime = 'Breakout Confirmed'

            elif last['low'] < recent_low:
                signal = 'SELL'
                entry = last['close']
                sl = recent_low * 1.01
                tp = entry - 3.0 * df['atr'].iloc[-1]
                regime = 'Breakout Confirmed'

    # بررسی نهایی منطقی بودن SL و TP
    if signal == 'BUY':
        if entry is None or sl is None or tp is None:
            return None
        if sl >= entry or tp <= entry or sl >= tp:
            return None

    elif signal == 'SELL':
        if entry is None or sl is None or tp is None:
            return None
        if sl <= entry or tp >= entry or sl <= tp:
            return None

    # فقط اگر سیگنال داشته باشیم، برگردانیم
    if signal:
        return {
            'signal': signal,
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'regime': regime
        }

    # اگر هیچ سیگنالی نبود
    return None
