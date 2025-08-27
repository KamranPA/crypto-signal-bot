# src/strategy/trend_strategy.py

import pandas as pd
from regime_detection.range_detector import is_range_regime

def apply_trend_strategy(df, adx_threshold=20, volume_ratio_threshold=1.2):
    """
    استراتژی روند با SL/TP تطبیقی بر اساس رژیم بازار
    """
    if len(df) < 50:
        return None

    # محاسبه EMA
    ema_21 = df['close'].ewm(span=21, adjust=False).mean()

    # محاسبه ATR
    tr1 = df['high'] - df['low']
    tr2 = abs(df['high'] - df['close'].shift(1))
    tr3 = abs(df['low'] - df['close'].shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean().iloc[-1]

    # محاسبه ADX
    def calculate_adx(high, low, close, window=14):
        # ... کد محاسبه ADX (همان قبلی)
        pass

    adx_value = calculate_adx(df['high'], df['low'], df['close'], 14).iloc[-1]
    volume_ratio = df['volume'].iloc[-1] / df['volume'].rolling(20).mean().iloc[-1]

    # تشخیص رژیم
    in_range = is_range_regime(df)
    strong_trend = adx_value >= 25
    weak_trend = adx_value >= 20 and adx_value < 25

    # تعیین ضریب SL و TP بر اساس رژیم
    if strong_trend and not in_range:
        sl_mult = 1.0
        tp_mult = 3.0
        regime = 'Strong Trend_Up' if df['close'].iloc[-1] > ema_21.iloc[-1] else 'Strong Trend_Down'
    elif in_range:
        sl_mult = 0.6
        tp_mult = 1.8
        regime = 'Range_Mean_Reversion'
    elif weak_trend:
        sl_mult = 1.4
        tp_mult = 2.4
        regime = 'Weak Trend'
    else:
        sl_mult = 1.3
        tp_mult = 2.8
        regime = 'Normal Trend'

    # بررسی سیگنال
    if adx_value >= adx_threshold and volume_ratio >= volume_ratio_threshold:
        # خرید
        if df['close'].iloc[-1] > ema_21.iloc[-1] and df['close'].iloc[-2] <= ema_21.iloc[-2]:
            entry = df['close'].iloc[-1]
            sl = entry - sl_mult * atr
            tp = entry + tp_mult * atr

            if sl >= entry or tp <= entry or sl >= tp:
                return None

            return {
                'signal': 'BUY',
                'entry': entry,
                'stop_loss': sl,
                'take_profit': tp,
                'regime': regime,
                'sl_mult': sl_mult,
                'tp_mult': tp_mult,
                'risk_reward': tp_mult / sl_mult  # مثلاً 3.0
            }

        # فروش
        elif df['close'].iloc[-1] < ema_21.iloc[-1] and df['close'].iloc[-2] >= ema_21.iloc[-2]:
            entry = df['close'].iloc[-1]
            sl = entry + sl_mult * atr
            tp = entry - tp_mult * atr

            if sl <= entry or tp >= entry or sl <= tp:
                return None

            return {
                'signal': 'SELL',
                'entry': entry,
                'stop_loss': sl,
                'take_profit': tp,
                'regime': regime,
                'sl_mult': sl_mult,
                'tp_mult': tp_mult,
                'risk_reward': tp_mult / sl_mult
            }

    return None
