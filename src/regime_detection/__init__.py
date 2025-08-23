"""
این فایل اجازه می‌دهد که ماژول‌های تشخیص رژیم به راحتی وارد شوند.
مثال:
    from src.regime_detection import is_trend_regime, is_range_regime
"""

# وارد کردن توابع از فایل‌های داخلی
from .range_detector import is_range_regime
from .trend_detector import is_trend_regime
from .breakout_detector import is_breakout_regime

# تعریف __all__ برای کنترل واردات عمومی (مثلاً با from ... import *)
__all__ = [
    'is_range_regime',
    'is_trend_regime',
    'is_breakout_regime'
]
