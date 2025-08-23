# src/strategy/trading_system.py
from src.regime_detection.range_detector import is_range_regime
from src.regime_detection.trend_detector import is_trend_regime
from src.regime_detection.breakout_detector import is_breakout_regime
import numpy as np

def generate_signal(df):
    # محاسبه شاخص‌های لازم
    df['sma_20'] = df['close'].rolling(20).mean()
    df['sma_50'] = df['close'].rolling(50).mean()
    df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()

    # تشخیص رژیم
    in_range = is_range_regime(df)
    in_trend = is_trend_regime(df)
    in_breakout = is_breakout_regime(df)

    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]

    signal = None
    entry = sl = tp = None

    # تعیین حد سود و ضرر پویا
    atr_value = last_row['atr']
    tp_multiplier = 2.0
    sl_multiplier = 1.0

    if in_trend and last_row['sma_20'] > last_row['sma_50'] and prev_row['sma_20'] <= prev_row['sma_50']:
        signal = 'BUY'
        entry = last_row['close']
        sl = entry - sl_multiplier * atr_value
        tp = entry + tp_multiplier * atr_value

    elif in_trend and last_row['sma_20'] < last_row['sma_50'] and prev_row['sma_20'] >= prev_row['sma_50']:
        signal = 'SELL'
        entry = last_row['close']
        sl = entry + sl_multiplier * atr_value
        tp = entry - tp_multiplier * atr_value

    elif in_range:
        lower_band = df['low'].rolling(20).min().iloc[-1]
        upper_band = df['high'].rolling(20).max().iloc[-1]
        if abs(last_row['close'] - lower_band) / lower_band < 0.005:
            signal = 'BUY'
            entry = last_row['close']
            sl = lower_band * 0.99
            tp = entry + 1.5 * atr_value
        elif abs(last_row['close'] - upper_band) / upper_band < 0.005:
            signal = 'SELL'
            entry = last_row['close']
            sl = upper_band * 1.01
            tp = entry - 1.5 * atr_value

    elif in_breakout:
        if last_row['high'] > df['high'].rolling(20).max().iloc[-2]:
            signal = 'BUY'
            entry = last_row['close']
            sl = entry - 1.2 * atr_value
            tp = entry + 2.5 * atr_value
        elif last_row['low'] < df['low'].rolling(20).min().iloc[-2]:
            signal = 'SELL'
            entry = last_row['close']
            sl = entry + 1.2 * atr_value
            tp = entry - 2.5 * atr_value

    return {
        'signal': signal,
        'entry': entry,
        'stop_loss': sl,
        'take_profit': tp,
        'regime': 'Trend' if in_trend else 'Range' if in_range else 'Breakout' if in_breakout else 'Uncertain'
    }
