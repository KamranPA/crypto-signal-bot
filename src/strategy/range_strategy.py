# src/strategy/range_strategy.py

import pandas as pd
from regime_detection.range_detector import is_range_regime

def apply_range_strategy(df, window=20):
    """
    استراتژی رنج: فقط در بازارهای رنج
    """
    if len(df) < window + 1:
        print("⚠️ range_strategy: داده کافی نیست")
        return None

    in_range = is_range_regime(df)
    print(f"🔍 range_strategy: آیا بازار رنج است؟ {in_range}")

    if not in_range:
        print("❌ بازار رنج نیست — استراتژی رنج فعال نمی‌شود")
        return None

    close = df['close']
    mean_price = close.rolling(window).mean().iloc[-1]
    std_price = close.rolling(window).std().iloc[-1]
    z_score = (close.iloc[-1] - mean_price) / std_price

    print(f"📊 وضعیت رنج:")
    print(f"   میانگین: {mean_price:.6f}")
    print(f"   انحراف معیار: {std_price:.6f}")
    print(f"   Z-Score: {z_score:.2f}")

    if abs(z_score) < 1.5:
        print("❌ Z-Score کافی نیست — نزدیک به میانگین")
        return None

    # محاسبه ATR
    tr1 = df['high'] - df['low']
    tr2 = abs(df['high'] - df['close'].shift(1))
    tr3 = abs(df['low'] - df['close'].shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean().iloc[-1]

    if z_score < -1.5:
        entry = close.iloc[-1]
        sl = entry - 0.5 * std_price
        tp = mean_price
        if sl >= entry or tp <= entry:
            print("❌ حد ضرر یا حد سود نامعتبر است")
            return None
        print(f"✅ سیگنال خرید رنج: ورود={entry:.6f}, SL={sl:.6f}, TP={tp:.6f}")
        return {
            'signal': 'BUY',
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'regime': 'Range_Mean_Reversion'
        }
    elif z_score > 1.5:
        entry = close.iloc[-1]
        sl = entry + 0.5 * std_price
        tp = mean_price
        if sl <= entry or tp >= entry:
            print("❌ حد ضرر یا حد سود نامعتبر است")
            return None
        print(f"✅ سیگنال فروش رنج: ورود={entry:.6f}, SL={sl:.6f}, TP={tp:.6f}")
        return {
            'signal': 'SELL',
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'regime': 'Range_Mean_Reversion'
        }

    return None
