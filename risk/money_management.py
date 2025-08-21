# risk/money_management.py

def calculate_sl_tp(entry_price, atr, signal, risk_reward_ratio):
    if signal == 1:  # Long
        sl = entry_price - 1.5 * atr
        tp = entry_price + (1.5 * atr * risk_reward_ratio)
    elif signal == -1:  # Short
        sl = entry_price + 1.5 * atr
        tp = entry_price - (1.5 * atr * risk_reward_ratio)
    else:
        sl = tp = entry_price
    return round(sl, 2), round(tp, 2)
