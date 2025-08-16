# utils/detect_bos.py
def detect_bos(high, low, lookback=100):
    if len(high) < lookback + 5:
        return None

    # تشخیص HH و LL
    recent_highs = list(high[-lookback:])
    recent_lows = list(low[-lookback:])

    hh = max(recent_highs)
    ll = min(recent_lows)

    idx_hh = recent_highs.index(hh)
    idx_ll = recent_lows.index(ll)

    current_price = high[-1]

    # BOS نزولی: قیمت زیر HL قبلی برود
    for i in range(-5, -2):
        if low[i] > low[i-1] and low[i] > low[i+1]:  # HL
            if current_price < low[i]:
                return 'bearish'

    # BOS صعودی: قیمت بالاتر از HH قبلی برود
    for i in range(-5, -2):
        if high[i] < high[i-1] and high[i] < high[i+1]:  # LH
            if current_price > high[i]:
                return 'bullish'

    return None
