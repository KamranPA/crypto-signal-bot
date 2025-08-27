# src/strategy/trading_system.py

"""
مدیریت استراتژی‌های معاملاتی
ترتیب اولویت:
1. شکست (Breakout)
2. روند (Trend)
3. رنج (Range)
"""

# ✅ وارد کردن استراتژی‌ها با relative import
from .trend_strategy import apply_trend_strategy
from .range_strategy import apply_range_strategy
from .breakout_strategy import apply_breakout_strategy


def get_signal(df):
    """
    تولید سیگنال بر اساس ترکیب استراتژی‌ها
    :param df: داده کندلی (pandas.DataFrame)
    :return: دیکشنری شامل سیگنال و جزئیات یا None
    """
    if len(df) < 50:
        return None

    try:
        # --- 1. استراتژی شکست ---
        signal = apply_breakout_strategy(df)
        if signal is not None:
            # اضافه کردن اولویت
            signal['priority'] = 1
            signal['strategy'] = 'Breakout'
            return signal

        # --- 2. استراتژی روند ---
        signal = apply_trend_strategy(df)
        if signal is not None:
            signal['priority'] = 2
            signal['strategy'] = 'Trend'
            return signal

        # --- 3. استراتژی رنج ---
        signal = apply_range_strategy(df)
        if signal is not None:
            signal['priority'] = 3
            signal['strategy'] = 'Range'
            return signal

        # --- هیچ سیگنالی تولید نشد ---
        return None

    except Exception as e:
        print(f"❌ خطا در get_signal: {e}")
        return None


# --- برای تست دستی (اختیاری) ---
if __name__ == "__main__":
    import pandas as pd
    # این بخش فقط برای تست محلی است
    print("✅ trading_system.py با موفقیت بارگذاری شد.")
    print("📌 توابع موجود:")
    print("   - apply_trend_strategy")
    print("   - apply_range_strategy")
    print("   - apply_breakout_strategy")
    print("   - get_signal")
