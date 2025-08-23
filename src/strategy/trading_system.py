# src/strategy/trading_system.py
from src.regime_detection.range_detector import is_range_regime
from src.regime_detection.trend_detector import is_trend_regime
from src.regime_detection.breakout_detector import is_breakout_regime
import ta

def generate_signal(df):
    if len(df) < 50:
        return {'signal': None}

    # محاسبه ATR برای حد سود/ضرر پویا
    atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14)
    df['atr'] = atr.average_true_range()
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]

    # تشخیص رژیم
    in_range = is_range_regime(df)
    in_trend = is_trend_regime(df)
    in_breakout = is_breakout_regime(df)

    signal = None
    entry = sl = tp = None

    # ضرایب حد سود و ضرر (از parameters.json هم می‌تونی بخونی)
    tp_mult = 2.0
    sl_mult = 1.0

    if in_trend and last_row['close'] > last_row['open']:
        if prev_row['close'] < prev_row['open'] and last_row['close'] > last_row['sma_20']:
            signal = 'BUY'
            entry = last_row['close']
            sl = entry - sl_mult * last_row['atr']
            tp = entry + tp_mult * last_row['atr']

    elif in_range:
        lower = df['low'].rolling(20).min().iloc[-1]
        upper = df['high'].rolling(20).max().iloc[-1]
        if abs(last_row['close'] - lower) / lower < 0.003:
            signal = 'BUY'
            entry = last_row['close']
            sl = lower * 0.99
            tp = entry + 1.5 * last_row['atr']

    elif in_breakout:
        if last_row['high'] > df['high'].rolling(20).max().iloc[-2]:
            signal = 'BUY'
            entry = last_row['close']
            sl = entry - 1.2 * last_row['atr']
            tp = entry + 2.5 * last_row['atr']

    return {
        'signal': signal,
        'entry': entry,
        'stop_loss': sl,
        'take_profit': tp,
        'regime': 'Trend' if in_trend else 'Range' if in_range else 'Breakout' if in_breakout else 'Uncertain'
    }
