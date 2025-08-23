# src/utils/config.py
import json
import os
from pathlib import Path

# مسیر فایل تنظیمات
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "parameters.json"

# بارگذاری تنظیمات
def load_config():
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"فایل تنظیمات یافت نشد: {CONFIG_PATH}")
    except json.JSONDecodeError as e:
        raise ValueError(f"خطا در خواندن JSON: {e}")

# ایجاد نمونه تنظیمات
config = load_config()

# دسترسی آسان به پارامترها
def get(key, default=None):
    """
    دسترسی آسان به تنظیمات با کلیدهای تو در تو
    مثال: get('strategy.trend.fast_sma')
    """
    keys = key.split('.')
    value = config
    try:
        for k in keys:
            value = value[k]
        return value
    except (KeyError, TypeError):
        return default
