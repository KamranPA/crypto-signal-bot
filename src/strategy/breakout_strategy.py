# src/strategy/breakout_strategy.py

def apply_breakout_strategy(df, volume_ratio_threshold=1.8):
    if not is_breakout_regime(df, volume_ratio_threshold=volume_ratio_threshold):
        return None

    # محاسبه ATR
    tr1 = df['high'] - df['low']
    tr2 = abs(df['high'] - df['close'].shift(1))
    tr3 = abs(df['low'] - df['close'].shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean().iloc[-1]

    # در شکست: SL/TP با تحمل نویز بیشتر
    sl_mult = 1.3
    tp_mult = 2.8

    # ... شرط شکست
    if df['high'].iloc[-1] > recent_high and df['close'].iloc[-1] > recent_high:
        entry = df['close'].iloc[-1]
        sl = recent_high * 0.995
        tp = entry + tp_mult * atr

        return {
            'signal': 'BUY',
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'regime': 'Breakout Confirmed',
            'risk_reward': tp_mult / sl_mult
        }
    # ... فروش
    return None
