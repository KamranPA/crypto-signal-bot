# src/strategy/trading_system.py
from src.regime_detection.range_detector import is_range_regime
from src.regime_detection.trend_detector import is_trend_regime
from src.regime_detection.breakout_detector import is_breakout_regime
import ta

def generate_signal(df):
    """
    تولید سیگنال بر اساس تشخیص رژیم بازار
    """
    if len(df) < 50:
        return {'signal': None, 'regime': 'Insufficient Data'}

    # محاسبه شاخص‌های لازم
    df['ema_21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
    df['atr'] = ta.volatility.AverageTrueRange(
        df['high'], df['low'], df['close'], window=14
    ).average_true_range()

    last = df.iloc[-1]
    prev = df.iloc[-2]
    volume_avg = df['volume'].rolling(20).mean().iloc[-1]

    # تشخیص رژیم
    in_trend = is_trend_regime(df)
    in_range = is_range_regime(df)
    in_breakout = is_breakout_regime(df)

    signal = None
    entry = sl = tp = None
    regime = 'Uncertain'

    # 🔹 روند (صعودی یا نزولی)
    if in_trend:
        regime = 'Trend'
        ema_slope = df['ema_21'].iloc[-1] - df['ema_21'].iloc[-3]

        # روند صعودی
        if ema_slope > 0 and last['close'] > last['ema_21']:
            if prev['close'] <= prev['ema_21'] and last['volume'] > volume_avg:
                signal = 'BUY'
                entry = last['close']
                sl = min(df['low'].iloc[-3:].min(), last['close'] - 1.5 * last['atr'])
                tp = entry + 2.5 * last['atr']

        # روند نزولی
        elif ema_slope < 0 and last['close'] < last['ema_21']:
            if prev['close'] >= prev['ema_21'] and last['volume'] > volume_avg:
                signal = 'SELL'
                entry = last['close']
                sl = max(df['high'].iloc[-3:].max(), last['close'] + 1.5 * last['atr'])
                tp = entry - 2.5 * last['atr']

    # 🔹 رنج (معامله در حمایت و مقاومت)
    elif in_range:
        regime = 'Range'
        lower_band = df['low'].rolling(20).min().iloc[-1]
        upper_band = df['high'].rolling(20).max().iloc[-1]

        if abs(last['close'] - lower_band) / lower_band < 0.005:
            signal = 'BUY'
            entry = last['close']
            sl = lower_band * 0.995
            tp = (lower_band + upper_band) / 2  # هدف: مرکز کانال

        elif abs(last['close'] - upper_band) / upper_band < 0.005:
            signal = 'SELL'
            entry = last['close']
            sl = upper_band * 1.005
            tp = (lower_band + upper_band) / 2

    # 🔹 شکست (با تأیید حجم و کندل)
    elif in_breakout:
        regime = 'Breakout'
        recent_high = df['high'].rolling(20).max().iloc[-2]
        recent_low = df['low'].rolling(20).min().iloc[-2]

        if last['high'] > recent_high:
            signal = 'BUY'
            entry = last['close']
            sl = recent_high * 0.99
            tp = entry + 3.0 * last['atr']

        elif last['low'] < recent_low:
            signal = 'SELL'
            entry = last['close']
            sl = recent_low * 1.01
            tp = entry - 3.0 * last['atr']

    return {
        'signal': signal,
        'entry': entry,
        'stop_loss': sl,
        'take_profit': tp,
        'regime': regime
    }
