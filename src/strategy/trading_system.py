# src/strategy/trading_system.py

from .trend_strategy import apply_trend_strategy
from .range_strategy import apply_range_strategy
from .breakout_strategy import apply_breakout_strategy

def get_signal(df):
    if len(df) < 50:
        return None

    try:
        # 1. شکست
        signal = apply_breakout_strategy(df)
        if signal:
            signal['priority'] = 1
            signal['strategy'] = 'Breakout'
            return signal

        # 2. روند
        signal = apply_trend_strategy(df)
        if signal:
            signal['priority'] = 2
            signal['strategy'] = 'Trend'
            return signal

        # 3. رنج
        signal = apply_range_strategy(df)
        if signal:
            signal['priority'] = 3
            signal['strategy'] = 'Range'
            return signal

        return None

    except Exception as e:
        print(f"❌ خطا در get_signal: {e}")
        return None
