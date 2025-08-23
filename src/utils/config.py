# src/utils/config.py
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "parameters.json"

def load_config():
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"خطا در بارگذاری تنظیمات: {e}")

config = load_config()

def get(key, default=None):
    keys = key.split('.')
    data = config
    for k in keys:
        if isinstance(data, dict) and k in data:
            data = data[k]
        else:
            return default
    return data
