# utils/detect_fvg.py
def detect_fvg(high, low, close, threshold=0.001):
    if len(high) < 3:
        return None

    # FVG: شکاف بین شمع‌ها
    mid1 = (high[-3] + low[-3]) / 2
    mid2 = (high[-2] + low[-2]) / 2
    mid3 = (high[-1] + low[-1]) / 2

    # Bullish FVG: شمع وسط پایین‌تر، دو طرف بالاتر
    if high[-3] > low[-2] and high[-1] > low[-2] and low[-2] < min(low[-3], low[-1]):
        mid = (high[-2] + low[-2]) / 2
        size = mid - low[-2]
        if size / mid > threshold:
            return {'type': 'bullish', 'zone': (low[-2], min(high[-3], high[-1])), 'mid': mid}

    # Bearish FVG: شمع وسط بالاتر، دو طرف پایین‌تر
    elif low[-3] < high[-2] and low[-1] < high[-2] and high[-2] > max(high[-3], high[-1]):
        mid = (high[-2] + low[-2]) / 2
        size = high[-2] - mid
        if size / mid > threshold:
            return {'type': 'bearish', 'zone': (max(low[-3], low[-1]), high[-2]), 'mid': mid}

    return None
