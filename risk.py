# risk.py

def dynamic_stop_loss(entry_price, atr, direction="long"):
    """
    محاسبه حد ضرر و حد سود بر اساس ATR
    :param entry_price: قیمت ورود
    :param atr: ATR فعلی
    :param direction: 'long' یا 'short'
    :return: stop_loss, take_profit
    """
    sl_multiplier = 1.5
    tp_multiplier = 3.0  # نسبت 2:1 (3.0 / 1.5 = 2)

    if direction == "long":
        stop_loss = entry_price - (sl_multiplier * atr)
        take_profit = entry_price + (tp_multiplier * atr)
    else:  # short
        stop_loss = entry_price + (sl_multiplier * atr)
        take_profit = entry_price - (tp_multiplier * atr)

    return stop_loss, take_profit


def position_size(capital, risk_percent=0.01, stop_loss_distance=None, price=None):
    """
    محاسبه حجم معامله بر اساس مدیریت ریسک
    :param capital: سرمایه
    :param risk_percent: درصد ریسک هر معامله (مثلاً 1%)
    :param stop_loss_distance: فاصله قیمت تا حد ضرر
    :param price: قیمت ورود
    :return: حجم معامله (مثلاً 0.01 BTC)
    """
    if stop_loss_distance is None or stop_loss_distance <= 0 or price is None:
        # اگر فاصله حد ضرر نامعتبر باشد، فقط 1% سرمایه را ریسک کن
        return capital * 0.01 / price if price else 0.01

    risk_per_unit = stop_loss_distance
    risk_amount = capital * risk_percent
    size = risk_amount / risk_per_unit

    return size


def calculate_risk_reward_ratio(atr, direction="long", reward_multiplier=2.0):
    """
    محاسبه نسبت سود به ضرر بر اساس ATR
    :param atr: ATR
    :param direction: 'long' یا 'short'
    :param reward_multiplier: چند برابر ریسک سود بگیریم؟ (مثلاً 2.0 = 2:1)
    :return: نسبت سود به ضرر
    """
    risk = 1.5 * atr
    reward = reward_multiplier * risk
    return reward / risk
