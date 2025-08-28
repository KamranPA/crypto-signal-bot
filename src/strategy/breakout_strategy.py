# src/strategy/breakout_strategy.py

import pandas as pd

def apply_breakout_strategy(df, volume_ratio_threshold=1.8, min_body_ratio=0.6):
    """
    استراتژی شکست: فقط در شرایط شکست قوی و با تأیید حجم
    """
    if len(df) < 50:
        print("⚠️ breakout_strategy: تعداد کندل‌ها کمتر از 50 است")
        return None

    print(f"📊 breakout_strategy: بررسی {len(df)} کندل")

    # --- محاسبه ATR ---
    tr1 = df['high'] - df['low']
    tr2 = abs(df['high'] - df['close'].shift(1))
    tr3 = abs(df['low'] - df['close'].shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean().iloc[-1]

    # --- بررسی حجم ---
    volume_avg = df['volume'].rolling(20).mean().iloc[-1]
    volume_ratio = df['volume'].iloc[-1] / volume_avg
    print(f"📈 حجم: نسبت = {volume_ratio:.2f} | حداقل: {volume_ratio_threshold}")

    if volume_ratio < volume_ratio_threshold:
        print("❌ حجم کافی نیست — شکست تأیید نشد")
        return None

    # --- بررسی بدن کندل ---
    body_size = abs(df['close'].iloc[-1] - df['open'].iloc[-1])
    if body_size < min_body_ratio * atr:
        print("❌ بدن کندل کوچک است — شکست قوی نیست")
        return None

    # --- شناسایی شکست بالا ---
    recent_high = df['high'].rolling(20).max().iloc[-2]
    current_high = df['high'].iloc[-1]
    current_close = df['close'].iloc[-1]

    if current_high > recent_high and current_close > recent_high:
        entry = current_close
        # حد ضرر: کمی زیر شکست (جلوگیری از شکست کاذب)
        sl = recent_high * 0.995
        # حد سود: نسبت به ATR
        tp = entry + 2.8 * atr

        if sl >= entry or tp <= entry or sl >= tp:
            print("❌ حد ضرر یا حد سود نامعتبر است")
            return None

        print(f"✅ سیگنال خرید شکست: ورود={entry:.6f}, SL={sl:.6f}, TP={tp:.6f}")
        return {
            'signal': 'BUY',
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'regime': 'Breakout Confirmed',
            'volume_ratio': volume_ratio,
            'atr': atr
        }

    # --- شناسایی شکست پایین ---
    recent_low = df['low'].rolling(20).min().iloc[-2]
    current_low = df['low'].iloc[-1]

    if current_low < recent_low and current_close < recent_low:
        entry = current_close
        # حد ضرر: کمی بالاتر از شکست
        sl = recent_low * 1.005
        # حد سود: نسبت به ATR
        tp = entry - 2.8 * atr

        if sl <= entry or tp >= entry or sl <= tp:
            print("❌ حد ضرر یا حد سود نامعتبر است")
            return None

        print(f"✅ سیگنال فروش شکست: ورود={entry:.6f}, SL={sl:.6f}, TP={tp:.6f}")
        return {
            'signal': 'SELL',
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'regime': 'Breakout Confirmed',
            'volume_ratio': volume_ratio,
            'atr': atr
        }

    print("❌ شرایط شکست برقرار نیست")
    return None
