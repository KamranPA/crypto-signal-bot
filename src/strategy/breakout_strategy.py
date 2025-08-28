# src/strategy/breakout_strategy.py

import pandas as pd
from regime_detection.breakout_detector import is_breakout_regime

def apply_breakout_strategy(df, volume_ratio_threshold=1.8, min_body_ratio=0.6):
    """
    استراتژی شکست: فقط در شرایط شکست
    """
    if len(df) < 50:
        print("⚠️ breakout_strategy: داده کافی نیست")
        return None

    # محاسبه حجم
    volume_avg = df['volume'].rolling(20).mean().iloc[-1]
    volume_ratio = df['volume'].iloc[-1] / volume_avg

    print(f"🔍 breakout_strategy: حجم نسبی = {volume_ratio:.2f} | حداقل: {volume_ratio_threshold}")

    if volume_ratio < volume_ratio_threshold:
        print("❌ حجم کافی نیست — شکست تأیید نشد")
        return None

    # بررسی بدن کندل
    body_size = abs(df['close'].iloc[-1] - df['open'].iloc[-1])
    tr = (df['high'] - df['low']).rolling(14).mean().iloc[-1]

    if body_size < min_body_ratio * tr:
        print("❌ بدن کندل کوچک است — شکست قوی نیست")
        return None

    # شرط شکست بالا
    recent_high = df['high'].rolling(20).max().iloc[-2]
    if df['high'].iloc[-1] > recent_high and df['close'].iloc[-1] > recent_high:
        entry = df['close'].iloc[-1]
        sl = recent_high * 0.995
        tp = entry + 2.5 * tr
        if sl >= entry or tp <= entry or sl >= tp:
            print("❌ حد ضرر یا حد سود نامعتبر است")
            return None
        print(f"✅ سیگنال شکست خرید: ورود={entry:.6f}, SL={sl:.6f}, TP={tp:.6f}")
        return {
            'signal': 'BUY',
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'regime': 'Breakout Confirmed'
        }

    # شرط شکست پایین
    recent_low = df['low'].rolling(20).min().iloc[-2]
    if df['low'].iloc[-1] < recent_low and df['close'].iloc[-1] < recent_low:
        entry = df['close'].iloc[-1]
        sl = recent_low * 1.005
        tp = entry - 2.5 * tr
        if sl <= entry or tp >= entry or sl <= tp:
            print("❌ حد ضرر یا حد سود نامعتبر است")
            return None
        print(f"✅ سیگنال شکست فروش: ورود={entry:.6f}, SL={sl:.6f}, TP={tp:.6f}")
        return {
            'signal': 'SELL',
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'regime': 'Breakout Confirmed'
        }

    print("❌ شرایط شکست برقرار نیست")
    return None
