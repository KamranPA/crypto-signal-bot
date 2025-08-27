# src/strategy/__init__.py

from .trend_strategy import apply_trend_strategy
from .range_strategy import apply_range_strategy
from .breakout_strategy import apply_breakout_strategy
from .trading_system import get_signal

__all__ = [
    'apply_trend_strategy',
    'apply_range_strategy',
    'apply_breakout_strategy',
    'get_signal'
]
