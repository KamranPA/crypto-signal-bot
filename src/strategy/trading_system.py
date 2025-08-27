# src/strategy/trading_system.py

from trend_strategy import apply_trend_strategy
from range_strategy import apply_range_strategy
from breakout_strategy import apply_breakout_strategy

def get_signal(df):
    if len(df) < 50:
        return None

    try:
        signal = apply_breakout_strategy(df)
        if signal:
            return signal

        signal = apply_trend_strategy(df)
        if signal:
            return signal

        signal = apply_range_strategy(df)
        if signal:
            return signal

        return None
    except Exception:
        return None
