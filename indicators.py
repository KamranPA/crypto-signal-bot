# indicators.py
import numpy as np
import pandas as pd

def ema(data, period):
    return pd.Series(data).ewm(span=period, adjust=False).mean().values

def rsi(data, period=14):
    delta = np.diff(data)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(period).mean()
    avg_loss = pd.Series(loss).rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def find_swing_low(low, window=5):
    """پیدا کردن آخرین نقطه کمینه محلی"""
    for i in range(len(low) - window - 1, 0, -1):
        if all(low[i] < low[i - j] for j in range(1, window + 1)) and \
           all(low[i] < low[i + j] for j in range(1, window + 1)):
            return low[i]
    return None

def find_swing_high(high, window=5):
    """پیدا کردن آخرین نقطه بیشینه محلی"""
    for i in range(len(high) - window - 1, 0, -1):
        if all(high[i] > high[i - j] for j in range(1, window + 1)) and \
           all(high[i] > high[i + j] for j in range(1, window + 1)):
            return high[i]
    return None

def fibo_extension(entry, swing_low, ratio):
    return entry + ratio * (entry - swing_low)
