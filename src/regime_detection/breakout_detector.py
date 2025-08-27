# src/regime_detection/breakout_detector.py

from .range_detector import is_range_regime

def is_breakout_regime(df, window=20, volume_ratio_threshold=1.3):
    """
    تشخیص شکست واقعی: فقط پس از بازار رنج و با تأیید حجم و کندل
    """
    if len(df) < window + 2:
        return False

    # 1. آیا قبل از شکست، بازار در رنج بوده؟ (مثلاً 3 کندل آخر)
    recent_df = df.iloc[-window-2:-2]  # دوره قبل از شکست
    if not is_range_regime(recent_df):
        return False  # بدون رنج، شکست معتبر نیست

    # 2. مقاومت و حمایت محلی (مثلاً 20 کندل قبل از آخرین دو کندل)
    recent_high = df['high'].rolling(window).max().iloc[-2]
    recent_low = df['low'].rolling(window).min().iloc[-2]

    current = df.iloc[-1]
    prev = df.iloc[-2]

    # 3. تأیید شکست:
    # - کندل فعلی بالاتر/پایین‌تر از مقاومت/حمایت بوده باشد
    # - بسته شدن در جهت شکست
    confirmed_up = current['high'] > recent_high and current['close'] > prev['close']
    confirmed_down = current['low'] < recent_low and current['close'] < prev['close']

    # 4. حجم: بالاتر از میانگین 20 دوره‌ای
    volume_avg = df['volume'].rolling(window).mean().iloc[-1]
    volume_ratio = current['volume'] / volume_avg

    return (confirmed_up or confirmed_down) and (volume_ratio > volume_ratio_threshold)
