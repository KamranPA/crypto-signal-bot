def dynamic_stop_loss(entry_price, atr, direction="long", rr_ratio=3.0):
    """
    محاسبه حد ضرر و حد سود با نسبت سود به ضرر مشخص (مثلاً 3:1)
    """
    sl_multiplier = 1.0  # حد ضرر = 1.0 × ATR
    tp_multiplier = sl_multiplier * rr_ratio

    if direction == "long":
        stop_loss = entry_price - (sl_multiplier * atr)
        take_profit = entry_price + (tp_multiplier * atr)
    else:
        stop_loss = entry_price + (sl_multiplier * atr)
        take_profit = entry_price - (tp_multiplier * atr)

    return stop_loss, take_profit

def position_size(capital, risk_percent=0.01, stop_loss_distance=None, price=None):
    """
    محاسبه حجم معامله بر اساس ریسک ثابت
    """
    if stop_loss_distance is None or stop_loss_distance <= 0 or price is None or price == 0:
        return capital * 0.01 / 100  # مقدار کوچک فرضی

    risk_per_unit = stop_loss_distance
    risk_amount = capital * risk_percent
    size = risk_amount / risk_per_unit

    return size
