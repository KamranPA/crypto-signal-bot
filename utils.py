# utils.py
import json
from datetime import datetime, timezone, timedelta

def load_signals(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}

def save_signals(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def is_new_candle_closed(candle_time):
    now = datetime.now(timezone.utc)
    candle_end = candle_time + timedelta(minutes=15)
    return (now - candle_end).total_seconds() > 60  # حداقل 1 دقیقه از بسته شدن گذشته
