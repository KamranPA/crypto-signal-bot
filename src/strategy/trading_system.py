# src/strategy/trading_system.py

from .trend_strategy import apply_trend_strategy
from .range_strategy import apply_range_strategy
from .breakout_strategy import apply_breakout_strategy

def get_signal(df):
    """
    مدیریت اولویت استراتژی‌ها:
    1. شکست
    2. روند
    3. رنج
    """
    if len(df) < 50:
        return None

    try:
        # 1. شکست
        signal = apply_breakout_strategy(df)
        if signal is not None:
            return {**signal, 'priority': 1}

        # 2. روند
        signal = apply_trend_strategy(df)
        if signal is not None:
            return {**signal, 'priority': 2}

        # 3. رنج
        signal = apply_range_strategy(df)
        if signal is not None:
            return {**signal, 'priority': 3}

        return None

    except Exception as e:
        print(f"Error in get_signal: {e}")
        return None
