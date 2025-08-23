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

    last = df.iloc[-1]
    prev = df.iloc[-2]
    volume_avg = df['volume'].rolling(20).mean().iloc[-1]

    in_trend = is_trend_regime(df)
    in_range = is_range_regime(df)
    in_breakout = is_breakout_regime(df)

    signal = entry = sl = tp = None
    regime = 'Uncertain'

    # 🔹 روند صعودی
    if in_trend and last['close'] > last['ema_21']:
        if prev['close'] <= prev['ema_21'] and last['volume'] > volume_avg:
            signal = 'BUY'
            entry = last['close']
            sl = entry - 1.5 * last['atr']  # پایین‌تر از ورود
            tp = entry + 2.5 * last['atr']  # بالاتر از ورود

            # ✅ بررسی منطقی بودن
            if sl >= entry or tp <= entry or sl >= tp:
                return {'signal': None, 'regime': 'Invalid SL/TP'}

    # 🔹 روند نزولی
    elif in_trend and last['close'] < last['ema_21']:
        if prev['close'] >= prev['ema_21'] and last['volume'] > volume_avg:
            signal = 'SELL'
            entry = last['close']
            sl = entry + 1.5 * last['atr']  # بالاتر از ورود
            tp = entry - 2.5 * last['atr']  # پایین‌تر از ورود

            # ✅ بررسی منطقی بودن
            if sl <= entry or tp >= entry or sl <= tp:
                return {'signal': None, 'regime': 'Invalid SL/TP'}

    # 🔹 رنج
    elif in_range:
        lower = df['low'].rolling(20).min().iloc[-1]
        upper = df['high'].rolling(20).max().iloc[-1]

        if abs(last['close'] - lower) / lower < 0.005:
            signal = 'BUY'
            entry = last['close']
            sl = lower * 0.995
            tp = (lower + upper) / 2

            if sl >= entry or tp <= entry or sl >= tp:
                return {'signal': None, 'regime': 'Invalid SL/TP'}

        elif abs(last['close'] - upper) / upper < 0.005:
            signal = 'SELL'
            entry = last['close']
            sl = upper * 1.005
            tp = (lower + upper) / 2

            if sl <= entry or tp >= entry or sl <= tp:
                return {'signal': None, 'regime': 'Invalid SL/TP'}

    # 🔹 شکست
    elif in_breakout:
        recent_high = df['high'].rolling(20).max().iloc[-2]
        recent_low = df['low'].rolling(20).min().iloc[-2]

        if last['high'] > recent_high:
            signal = 'BUY'
            entry = last['close']
            sl = recent_high * 0.99
            tp = entry + 3.0 * last['atr']

            if sl >= entry or tp <= entry or sl >= tp:
                return {'signal': None, 'regime': 'Invalid SL/TP'}

        elif last['low'] < recent_low:
            signal = 'SELL'
            entry = last['close']
            sl = recent_low * 1.01
            tp = entry - 3.0 * last['atr']

            if sl <= entry or tp >= entry or sl <= tp:
                return {'signal': None, 'regime': 'Invalid SL/TP'}

    return {
        'signal': signal,
        'entry': entry,
        'stop_loss': sl,
        'take_profit': tp,
        'regime': regime
    }
