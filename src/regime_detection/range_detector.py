# src/regime_detection/range_detector.py

import pandas as pd
import numpy as np

def is_range_regime(df, window=20, volatility_threshold=0.7, volume_threshold=0.8):
    if len(df) < window + 1:
        return False

    true_range_pct = (df['high'] - df['low']) / df['close']
    avg_true_range_pct = true_range_pct.rolling(window).mean()
    current_volatility_pct = true_range_pct.iloc[-1]
    in_low_volatility = current_volatility_pct < avg_true_range_pct.iloc[-1] * volatility_threshold

    volume_ratio = df['volume'].iloc[-1] / df['volume'].rolling(window).mean().iloc[-1]
    in_low_volume = volume_ratio < volume_threshold

    high = df['high']
    low = df['low']
    close = df['close']

    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    up_move = high.diff()
    down_move = low.diff()
    pos_dm = ((up_move > down_move) & (up_move > 0)) * up_move
    neg_dm = ((down_move > up_move) & (down_move > 0)) * down_move

    alpha = 2 / (window + 1)
    smoothed_pos_dm = pos_dm.ewm(alpha=alpha, min_periods=1).mean()
    smoothed_neg_dm = neg_dm.ewm(alpha=alpha, min_periods=1).mean()
    atr = tr.ewm(alpha=alpha, min_periods=1).mean()

    di_plus = (smoothed_pos_dm / atr) * 100
    di_minus = (smoothed_neg_dm / atr) * 100
    dx = abs(di_plus - di_minus) / (di_plus + di_minus + 1e-8) * 100
    adx = dx.ewm(alpha=alpha, min_periods=1).mean()

    in_no_trend = adx.iloc[-1] < 20

    return in_low_volatility and in_low_volume and in_no_trend
