# src/utils/indicators.py

import pandas as pd
import numpy as np

def calculate_atr(high, low, close, window=14):
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(alpha=1/window, adjust=False).mean()

def calculate_adx(high, low, close, window=14):
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    up_move = high.diff()
    down_move = low.diff()
    pos_dm = ((up_move > down_move) & (up_move > 0)) * up_move
    neg_dm = ((down_move > up_move) & (down_move > 0)) * down_move

    alpha = 1 / window
    smoothed_pos_dm = pos_dm.ewm(alpha=alpha, adjust=False).mean()
    smoothed_neg_dm = neg_dm.ewm(alpha=alpha, adjust=False).mean()
    atr = tr.ewm(alpha=alpha, adjust=False).mean()

    di_plus = (smoothed_pos_dm / atr) * 100
    di_minus = (smoothed_neg_dm / atr) * 100
    dx = abs(di_plus - di_minus) / (di_plus + di_minus + 1e-8) * 100
    adx = dx.ewm(alpha=alpha, adjust=False).mean()
    return adx

def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()
