# src/strategy/range_strategy.py

def apply_range_strategy(df, window=20):
    if not is_range_regime(df):
        return None

    # محاسبه ATR
    tr1 = df['high'] - df['low']
    tr2 = abs(df['high'] - df['close'].shift(1))
    tr3 = abs(df['low'] - df['close'].shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean().iloc[-1]

    # در رنج: SL/TP تنگ‌تر
    sl_mult = 0.5
    tp_mult = 1.5

    # ... محاسبه z-score
    if abs(z_score) >= 1.5:
        entry = close.iloc[-1]
        sl = entry - sl_mult * atr
        tp = entry + tp_mult * atr

        return {
            'signal': 'BUY' if z_score < -1.5 else 'SELL',
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'regime': 'Range_Mean_Reversion',
            'risk_reward': tp_mult / sl_mult
        }
    return None
