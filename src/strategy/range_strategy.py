# src/strategy/range_strategy.py

from ..regime_detection.range_detector import is_range_regime

def apply_range_strategy(df, window=20):
    """
    استراتژی رنج: بازگشت به میانگین (Mean Reversion)
    """
    if len(df) < window + 1:
        return None

    if not is_range_regime(df):
        return None  # فقط در رنج فعال می‌شود

    # محاسبه میانگین و انحراف معیار
    close = df['close']
    mean_price = close.rolling(window).mean().iloc[-1]
    std_price = close.rolling(window).std().iloc[-1]

    # فیلتر: فقط اگر قیمت در 1.5 SD از میانگین باشد
    z_score = (close.iloc[-1] - mean_price) / std_price
    if abs(z_score) < 1.5:
        return None

    # BUY: قیمت پایین از میانگین (زیر 1.5SD)
    if z_score < -1.5:
        entry = close.iloc[-1]
        sl = close.iloc[-1] - 0.5 * std_price
        tp = mean_price

        if sl >= entry or tp <= entry:
            return None

        return {
            'signal': 'BUY',
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'regime': 'Range_Mean_Reversion',
            'z_score': z_score
        }

    # SELL: قیمت بالا از میانگین (بالای 1.5SD)
    elif z_score > 1.5:
        entry = close.iloc[-1]
        sl = close.iloc[-1] + 0.5 * std_price
        tp = mean_price

        if sl <= entry or tp >= entry:
            return None

        return {
            'signal': 'SELL',
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'regime': 'Range_Mean_Reversion',
            'z_score': z_score
        }

    return None
