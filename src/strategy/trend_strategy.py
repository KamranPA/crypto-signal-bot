# src/strategy/trend_strategy.py

import pandas as pd
import numpy as np

from regime_detection.range_detector import is_range_regime

def apply_trend_strategy(df, adx_threshold=15, volume_ratio_threshold=1.0):
    """
    استراتژی روند: فقط در شرایط روند قوی و با تأیید حجم
    ✅ آستانه‌ها کاهش یافته برای تست
    """
    if len(df) < 50:
        return None

    # محاسبه EMA 21
    ema_21 = df['close'].ewm(span=21, adjust=False).mean()

    # محاسبه ADX بدون ta
    def calculate_adx(high, low, close, window=14):
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

        return adx

    adx_value = calculate_adx(df['high'], df['low'], df['close'], window=14).iloc[-1]
    volume_avg = df['volume'].rolling(20).mean().iloc[-1]
    volume_ratio = df['volume'].iloc[-1] / volume_avg

    # --- فیلتر رنج: فقط در غیررنج فعال شود ---
    if is_range_regime(df):
        return None

    # --- بررسی شرایط ---
    if adx_value >= adx_threshold and volume_ratio >= volume_ratio_threshold:
        if df['close'].iloc[-1] > ema_21.iloc[-1] and df['close'].iloc[-2] <= ema_21.iloc[-2]:
            entry = df['close'].iloc[-1]
            sl = entry * 0.95
            tp = entry * 1.05
            return {
                'signal': 'BUY',
                'entry': entry,
                'stop_loss': sl,
                'take_profit': tp,
                'regime': 'Strong Trend_Up'
            }
        elif df['close'].iloc[-1] < ema_21.iloc[-1] and df['close'].iloc[-2] >= ema_21.iloc[-2]:
            entry = df['close'].iloc[-1]
            sl = entry * 1.05
            tp = entry * 0.95
            return {
                'signal': 'SELL',
                'entry': entry,
                'stop_loss': sl,
                'take_profit': tp,
                'regime': 'Strong Trend_Down'
            }

    return None
