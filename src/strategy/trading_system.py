# src/strategy/trading_system.py
from src.regime_detection.range_detector import is_range_regime
from src.regime_detection.trend_detector import is_trend_regime
from src.regime_detection.breakout_detector import is_breakout_regime
import ta

def generate_signal(df):
    if len(df) < 50:
        return {'signal': None, 'regime': 'Insufficient Data'}

    # محاسبه شاخص‌ها
    df['ema_21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
    df['atr'] = ta.volatility.AverageTrueRange(
        df['high'], df['low'], df['close'], window=14
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

    last = df.iloc[-1]
    prev = df.iloc[-2]
    atr = last['atr']

    in_trend = is_trend_regime(df)
    in_range = is_range_regime(df)
    in_breakout = is_breakout_regime(df)

    signal = entry = sl = tp = None
    regime = 'Uncertain'

    # 🔹 روند: استفاده از ADX برای تأیید قدرت، نه مسدود کردن
    if in_trend:
        if adx_value > 25:
            regime = 'Strong Trend'
            if last['close'] > last['ema_21'] and prev['close'] <= prev['ema_21']:
                signal = 'BUY'
                entry = last['close']
                sl = entry - 1.5 * atr
                tp = entry + 2.5 * atr
            elif last['close'] < last['ema_21'] and prev['close'] >= prev['ema_21']:
                signal = 'SELL'
                entry = last['close']
                sl = entry + 1.5 * atr
                tp = entry - 2.5 * atr
        else:
            regime = 'Weak Trend'

    # 🔹 رنج: فقط اگر ADX پایین باشد (تأیید رنج)
    elif in_range:
        if adx_value < 20:
            regime = 'Range'
            lower = df['low'].rolling(20).min().iloc[-1]
            upper = df['high'].rolling(20).max().iloc[-1]

            if abs(last['close'] - lower) / lower < 0.005:
                signal = 'BUY'
                entry = last['close']
                sl = lower * 0.99
                tp = (lower + upper) / 2

            elif abs(last['close'] - upper) / upper < 0.005:
                signal = 'SELL'
                entry = last['close']
                sl = upper * 1.01
                tp = (lower + upper) / 2
        else:
            regime = 'Possible Breakout'

    # 🔹 شکست: تأیید با افزایش ADX
    elif in_breakout:
        adx_slope = adx_value - df['adx'].iloc[-2]
        if adx_slope > 0:
            regime = 'Breakout Confirmed'
            recent_high = df['high'].rolling(20).max().iloc[-2]
            recent_low = df['low'].rolling(20).min().iloc[-2]

            if last['high'] > recent_high:
                signal = 'BUY'
                entry = last['close']
                sl = recent_high * 0.99
                tp = entry + 3.0 * atr

            elif last['low'] < recent_low:
                signal = 'SELL'
                entry = last['close']
                sl = recent_low * 1.01
                tp = entry - 3.0 * atr
        else:
            regime = 'Fake Breakout?'

    # ✅ بررسی منطقی بودن SL/TP
    if signal == 'BUY':
        if sl >= entry or tp <= entry or sl >= tp:
            return {'signal': None, 'regime': 'Invalid SL/TP (BUY)'}
    elif signal == 'SELL':
        if sl <= entry or tp >= entry or sl <= tp:
            return {'signal': None, 'regime': 'Invalid SL/TP (SELL)'}

    return {
        'signal': signal,
        'entry': entry,
        'stop_loss': sl,
        'take_profit': tp,
        'regime': regime
    }
