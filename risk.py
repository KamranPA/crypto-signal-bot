def dynamic_stop_loss(entry_price, atr, direction="long"):
    sl = entry_price - (1.5 * atr) if direction == "long" else entry_price + (1.5 * atr)
    tp = entry_price + (3.0 * atr) if direction == "long" else entry_price - (3.0 * atr)  # 2:1
    return sl, tp

def position_size(capital, risk_percent=0.01, stop_loss_distance=None, price=None):
    if stop_loss_distance is None or stop_loss_distance == 0:
        return capital * 0.02
    risk_per_unit = stop_loss_distance
    risk_amount = capital * risk_percent
    size = risk_amount / risk_per_unit
    return size
