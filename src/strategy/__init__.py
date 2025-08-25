# src/strategy/__init__.py
"""
این فایل به پایتون می‌گوید که پوشه strategy یک ماژول است.
همچنین تابع اصلی generate_signal را برای وارد کردن آسان فراهم می‌کند.
"""

# وارد کردن تابع اصلی تولید سیگنال
from .trading_system import generate_signal

# (اختیاری) قرار دادن توابع دیگر در __all__ برای وارد کردن آسان
__all__ = ['generate_signal']
