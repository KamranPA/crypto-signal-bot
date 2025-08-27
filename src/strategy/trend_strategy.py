# src/strategy/trend_strategy.py

from regime_detection.range_detector import is_range_regime

def apply_trend_strategy(df, adx_threshold=20, volume_ratio_threshold=1.2):
    """
    استراتژی روند: فقط در شرایط روند قوی و با تأیید حجم
    ✅ رژیم‌محور: نه مسدود می‌شود توسط رنج، اما اولویت را می‌دهد
    """
    if len(df) < 50:
        return None

    # --- 1. محاسبه EMA 21 ---
    ema_21 = df['close'].ewm(span=21, adjust=False).mean()

    # --- 2. محاسبه ADX بدون ta ---
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

    # --- 3. محاسبه ATR ---
    tr1 = df['high'] - df['low']
    tr2 = abs(df['high'] - df['close'].shift(1))
    tr3 = abs(df['low'] - df['close'].shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean().iloc[-1]

    # --- 4. فیلتر حجم ---
    volume_avg = df['volume'].rolling(20).mean().iloc[-1]
    volume_ratio = df['volume'].iloc[-1] / volume_avg

    # --- 5. دیباگ: چاپ وضعیت فعلی ---
    print(f"📊 Trend Strategy Debug:")
    print(f"   ADX: {adx_value:.2f} (حداقل: {adx_threshold})")
    print(f"   حجم نسبی: {volume_ratio:.2f} (حداقل: {volume_ratio_threshold})")
    print(f"   رنج؟ {is_range_regime(df)}")

    # --- 6. شرط اصلی: روند قوی و حجم بالا ---
    if adx_value >= adx_threshold and volume_ratio >= volume_ratio_threshold:
        # BUY: عبور از EMA به سمت بالا
        if df['close'].iloc[-1] > ema_21.iloc[-1] and df['close'].iloc[-2] <= ema_21.iloc[-2]:
            entry = df['close'].iloc[-1]
            sl = min(df['low'].iloc[-2], entry - 1.5 * atr)
            tp = entry + 2.5 * atr

            if sl >= entry or tp <= entry or sl >= tp:
                return None

            return {
                'signal': 'BUY',
                'entry': entry,
                'stop_loss': sl,
                'take_profit': tp,
                'regime': 'Strong Trend_Up',
                'adx': adx_value,
                'volume_ratio': volume_ratio
            }

        # SELL: عبور از EMA به سمت پایین
        elif df['close'].iloc[-1] < ema_21.iloc[-1] and df['close'].iloc[-2] >= ema_21.iloc[-2]:
            entry = df['close'].iloc[-1]
            sl = max(df['high'].iloc[-2], entry + 1.5 * atr)
            tp = entry - 2.5 * atr

            if sl <= entry or tp >= entry or sl <= tp:
                return None

            return {
                'signal': 'SELL',
                'entry': entry,
                'stop_loss': sl,
                'take_profit': tp,
                'regime': 'Strong Trend_Down',
                'adx': adx_value,
                'volume_ratio': volume_ratio
            }

    return None
