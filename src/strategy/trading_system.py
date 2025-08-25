# src/strategy/trading_system.py
from .trend_strategy import apply_trend_strategy
from .range_strategy import apply_range_strategy
from .breakout_strategy import apply_breakout_strategy

def generate_signal(df):
    """
    تولید سیگنال با اولویت: روند > رنج > شکست
    """

    # 1. اولویت: روند
    trend_signal = apply_trend_strategy(df)
    if trend_signal:
        return trend_signal

    # 2. دوم: رنج
    range_signal = apply_range_strategy(df)
    if range_signal:
        return range_signal

    # 3. سوم: شکست
    breakout_signal = apply_breakout_strategy(df)
    if breakout_signal:
        return breakout_signal

    return None
