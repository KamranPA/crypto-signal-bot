# src/strategy/trading_system.py
from src.regime_detection.range_detector import is_range_regime
from src.regime_detection.trend_detector import is_trend_regime
from src.regime_detection.breakout_detector import is_breakout_regime
import ta

def generate_signal(df):
    if len(df) < 50:
        return None

    df['ema_21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
    df['atr'] = ta.volatility.AverageTrueRange(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=14
    ).average_true_range()

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
    volume_avg = df['volume'].rolling(20).mean().iloc[-1]
    volume_ratio = last['volume'] / volume_avg

    in_trend = is_trend_regime(df)
    in_range = is_range_regime(df)
    in_breakout = is_breakout_regime(df)

    signal = entry = sl = tp = None
    regime = 'Uncertain'

    if in_trend and adx_value > 25:
        if volume_ratio > 1.2:
            if last['close'] > last['ema_21'] and prev['close'] <= prev['ema_21']:
                signal = 'BUY'
                entry = last['close']
                sl = min(prev['low'], entry - 1.5 * df['atr'].iloc[-1])
                tp = entry + 2.5 * df['atr'].iloc[-1]
                regime = 'Strong Trend_Up'
            elif last['close'] < last['ema_21'] and prev['close'] >= prev['ema_21']:
                signal = 'SELL'
                entry = last['close']
                sl = max(prev['high'], entry + 1.5 * df['atr'].iloc[-1])
                tp = entry - 2.5 * df['atr'].iloc[-1]
                regime = 'Strong Trend_Down'

    elif in_range and adx_value < 20:
        regime = 'Range'
        lower_band = df['low'].rolling(20).min().iloc[-1]
        upper_band = df['high'].rolling(20).max().iloc[-1]
        if abs(last['close'] - lower_band) / lower_band < 0.005:
            signal = 'BUY'
            entry = last['close']
            sl = lower_band * 0.99
            tp = (lower_band + upper_band) / 2
        elif abs(last['close'] - upper_band) / upper_band < 0.005:
            signal = 'SELL'
            entry = last['close']
            sl = upper_band * 1.01
            tp = (lower_band + upper_band) / 2

    elif in_breakout:
        adx_slope = adx_value - df['adx'].iloc[-2]
        if adx_slope > 0 and volume_ratio > 1.3:
            recent_high = df['high'].rolling(20).max().iloc[-2]
            recent_low = df['low'].rolling(20).min().iloc[-2]
            if last['high'] > recent_high and last['close'] > recent_high:
                signal = 'BUY'
                entry = last['close']
                sl = recent_high * 0.99
                tp = entry + 2.5 * df['atr'].iloc[-1]
                regime = 'Breakout Confirmed'
            elif last['low'] < recent_low and last['close'] < recent_low:
                signal = 'SELL'
                entry = last['close']
                sl = recent_low * 1.01
                tp = entry - 2.5 * df['atr'].iloc[-1]
                regime = 'Breakout Confirmed'

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

    if signal:
        return {
            'signal': signal,
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'regime': regime
        }

    return None
