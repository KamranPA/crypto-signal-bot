# backtest.py
"""
بکتست ساده برای BTC/USDT با استفاده از KuCoin
بدون نمودار، بدون خطا، بدون پیچیدگی
"""

import ccxt
import pandas as pd
from datetime import datetime

# --- دریافت داده از KuCoin ---
def fetch_data():
    exchange = ccxt.kucoin({
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    
    # دریافت آخرین 100 کندل 15 دقیقه‌ای
    bars = exchange.fetch_ohlcv('BTC/USDT', '15m', limit=100)
    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

# --- محاسبه فیبوناچی و تشخیص ورود ---
def run_analysis(df):
    # آخرین 70 کندل
    recent = df.tail(70)
    
    if len(recent) < 70:
        print("❌ داده کافی برای تحلیل وجود ندارد")
        return
    
    recent_high = recent['high'].max()
    recent_low = recent['low'].min()
    current_price = df['close'].iloc[-1]
    
    # محاسبه سطوح فیبوناچی
    diff = recent_high - recent_low
    fib_71 = recent_low + 0.71 * diff
    
    print(f"📊 تحلیل BTC/USDT")
    print(f"📌 قیمت فعلی: {current_price:.2f}")
    print(f"📈 بالاترین (70 کندل): {recent_high:.2f}")
    print(f"📉 پایین‌ترین (70 کندل): {recent_low:.2f}")
    print(f"🎯 سطح 71% فیبوناچی: {fib_71:.2f}")
    
    # سیگنال ورود
    if current_price >= fib_71:
        print("🔻 سیگنال: SHORT (فروش)")
    else:
        print("🟢 وضعیت: صبر کنید")

# --- اجرای برنامه ---
if __name__ == '__main__':
    print("🔄 در حال دریافت داده از KuCoin...")
    try:
        df = fetch_data()
        print(f"✅ {len(df)} کندل دریافت شد")
        run_analysis(df)
    except Exception as e:
        print(f"❌ خطای ارتباط با صرافی: {e}")
