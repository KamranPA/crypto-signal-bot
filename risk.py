# risk.py
import numpy as np

def calculate_position_size(price, stop_loss_price, account_balance, risk_percent=0.02):
    """
    محاسبه حجم معامله بر اساس ریسک ثابت
    """
    risk_per_unit = abs(price - stop_loss_price)
    if risk_per_unit == 0:
        return 0
    risk_amount = account_balance * risk_percent
    position_size = risk_amount / risk_per_unit
    return position_size

def is_valid_signal(signal, volume_ratio, confidence, min_volume_ratio=1.5, min_confidence=0.3):
    """
    بررسی اعتبار سیگنال بر اساس ریسک
    """
    if signal == 0:
        return False
    if volume_ratio < min_volume_ratio:
        return False
    if confidence < min_confidence:
        return False
    return True

def apply_trailing_stop(current_price, entry_price, trail_percent=0.02):
    """
    محاسبه حد ضرر دنباله‌رو
    """
    if current_price > entry_price:
        return current_price * (1 - trail_percent)
    return None

def get_risk_level(win_rate, sharpe_ratio):
    """
    تعیین سطح ریسک بر اساس عملکرد
    """
    if win_rate > 0.6 and sharpe_ratio > 1.5:
        return "low"
    elif win_rate > 0.5 and sharpe_ratio > 1.0:
        return "medium"
    else:
        return "high"
