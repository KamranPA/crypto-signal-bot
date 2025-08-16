# backtest.py
"""
بکتست ساده برای BTC/USDT با استفاده از KuCoin
بدون خطا، بدون پیچیدگی
"""

import ccxt
import pandas as pd
import backtrader as bt
from datetime import datetime
import pytz

# --- دریافت داده از KuCoin ---
def fetch_data():
    exchange = ccxt.kucoin({
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    
    # دریافت آخرین 100 کندل 15 دقیقه‌ای
    bars = exchange.fetch_ohlcv('BTC/USDT', '15m', limit=100)
    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    df.set_index('timestamp', inplace=True)
    return df

# --- استراتژی ساده ---
class SimpleFibStrategy(bt.Strategy):
    def __init__(self):
        self.data_close = self.datas[0].close
        self.order = None

    def next(self):
        if self.order:
            return

        # اگر کمتر از 70 کندل داشته باشیم، صبر کن
        if len(self) < 70:
            return

        # محاسبه HH و LL برای 70 کندل آخر
        recent_high = max(self.data_high.get(-70, 70))
        recent_low = min(self.data_low.get(-70, 70))

        # محاسبه سطوح فیبوناچی
        diff = recent_high - recent_low
        fib_71 = recent_low + 0.71 * diff

        current_price = self.data_close[0]

        # ورود شورت در 71%
        if current_price >= fib_71:
            print(f"🔻 SHORT ENTRY at {current_price}")
            self.order = self.sell()
            self.buy(exectype=bt.Order.Stop, price=recent_high * 1.01, size=1)  # حد ضرر
            self.sell(exectype=bt.Order.Limit, price=recent_low, size=1)        # هدف

# --- اجرای بکتست ---
if __name__ == '__main__':
    # دریافت داده
    df = fetch_data()
    print(f"✅ {len(df)} کندل دریافت شد")

    # تنظیم backtrader
    cerebro = bt.Cerebro()
    data_feed = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data_feed)

    # افزودن استراتژی
    cerebro.addstrategy(SimpleFibStrategy)

    # تنظیمات بروکر
    cerebro.broker.setcash(10000)
    cerebro.broker.setcommission(commission=0.001)

    # اجرای بکتست
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.run()
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # نمایش نمودار (در محیط‌های گرافیکی)
    cerebro.plot(style='candlestick')
