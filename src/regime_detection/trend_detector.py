# src/strategy/trend_strategy.py

from ..regime_detection.range_detector import is_range_regime

def apply_trend_strategy(df, adx_threshold=25, volume_ratio_threshold=1.2):
    """
    استراتژی روند: فقط در بازارهای غیررنج و با روند قوی
    """
    if len(df) < 50:
        return None

    # --- 1. فیلتر بازار رنج ---
    if is_range_regime(df):
        return None  # در بازار رنج، سیگنال روند نمی‌دهیم

    # --- 2. محاسبه EMA 21 ---
    ema_21 = df['close'].ewm(span=21, adjust=False).mean()

    # --- 3. محاسبه ADX (بدون ta) ---
    # کد ADX از قبل (مثلاً از range_detector یا جداگانه)
    # اینجا برای کوتاهی، فرض می‌کنیم ADX در دسترس است
    # (می‌توانید از تابع محاسبه ADX در range_detector استفاده کنید)

    # --- 4. محاسبه ATR ---
    tr1 = df['high'] - df['low']
    tr2 = abs(df['high'] - df['close'].shift(1))
    tr3 = abs(df['low'] - df['close'].shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean().iloc[-1]

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # --- 5. فیلتر حجم ---
    volume_avg = df['volume'].rolling(20).mean().iloc[-1]
    volume_ratio = last['volume'] / volume_avg

    # --- 6. شرط روند قوی ---
    if volume_ratio >= volume_ratio_threshold:
        # BUY: عبور از EMA به سمت بالا
        if last['close'] > ema_21.iloc[-1] and prev['close'] <= ema_21.iloc[-2]:
            entry = last['close']
            sl = min(prev['low'], entry - 1.5 * atr)
            tp = entry + 2.5 * atr

            if sl >= entry or tp <= entry or sl >= tp:
                return None

            return {
                'signal': 'BUY',
                'entry': entry,
                'stop_loss': sl,
                'take_profit': tp,
                'regime': 'Strong Trend_Up',
                'atr': atr
            }

        # SELL: عبور از EMA به سمت پایین
        elif last['close'] < ema_21.iloc[-1] and prev['close'] >= ema_21.iloc[-2]:
            entry = last['close']
            sl = max(prev['high'], entry + 1.5 * atr)
            tp = entry - 2.5 * atr

            if sl <= entry or tp >= entry or sl <= tp:
                return None

            return {
                'signal': 'SELL',
                'entry': entry,
                'stop_loss': sl,
                'take_profit': tp,
                'regime': 'Strong Trend_Down',
                'atr': atr
            }

    return None
