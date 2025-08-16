# utils/detect_bos.py
def detect_bos(high, low, lookback=50):
    """
    تشخیص Break of Structure (BOS)
    - BOS نزولی: قیمت زیر یک HL قبلی برود
    - BOS صعودی: قیمت بالاتر از یک LH قبلی برود
    """
    if len(high) < lookback + 5:
        return None

    # BOS نزولی: شکست HL
    recent_highs = list(high.get(-lookback, lookback))
    recent_lows = list(low.get(-lookback, lookback))

    for i in range(-5, -2):
        if i >= -len(recent_lows): continue
        if recent_lows[i] > recent_lows[i-1] and recent_lows[i] > recent_lows[i+1]:  # HL
            if high[-1] < recent_lows[i]:
                return 'bearish'

    # BOS صعودی: شکست LH
    for i in range(-5, -2):
        if i >= -len(recent_highs): continue
        if recent_highs[i] < recent_highs[i-1] and recent_highs[i] < recent_highs[i+1]:  # LH
            if low[-1] > recent_highs[i]:
                return 'bullish'

    return None
