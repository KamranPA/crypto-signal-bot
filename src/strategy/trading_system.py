# src/strategy/trading_system.py

from .breakout_strategy import apply_breakout_strategy
from .trend_strategy import apply_trend_strategy
from .range_strategy import apply_range_strategy

def get_signal(df):
    if len(df) < 50:
        return None

    # اولویت: شکست > روند > رنج
    signal = apply_breakout_strategy(df)
    if signal:
        signal['priority'] = 1
        signal['strategy'] = 'Breakout'
        return signal

    signal = apply_trend_strategy(df)
    if signal:
        signal['priority'] = 2
        signal['strategy'] = 'Trend'
        return signal

    signal = apply_range_strategy(df)
    if signal:
        signal['priority'] = 3
        signal['strategy'] = 'Range'
        return signal

    return None
