# backtest.py (نسخه 2 - با backtrader اما بدون نمودار)
import ccxt
import pandas as pd
import backtrader as bt

class SimpleFibStrategy(bt.Strategy):
    def __init__(self):
        self.data_close = self.datas[0].close
        self.data_high = self.datas[0].high
        self.data_low = self.datas[0].low
        self.order = None

    def next(self):
        if self.order:
            return
        if len(self) < 70:
            return

        highs = self.data_high.get(-70, 70)
        lows = self.data_low.get(-70, 70)
        if len(highs) == 0 or len(lows) == 0:
            return

        recent_high = max(highs)
        recent_low = min(lows)
        fib_71 = recent_low + 0.71 * (recent_high - recent_low)
        current_price = self.data_close[0]

        if current_price >= fib_71:
            print(f"🔻 SHORT ENTRY at {current_price}")
            self.order = self.sell()
            self.buy(exectype=bt.Order.Stop, price=recent_high * 1.01, size=1)  # SL
            self.sell(exectype=bt.Order.Limit, price=recent_low, size=1)        # TP

# --- اجرای بکتست ---
if __name__ == '__main__':
    # دریافت داده
    exchange = ccxt.kucoin({'enableRateLimit': True})
    bars = exchange.fetch_ohlcv('BTC/USDT', '15m', limit=100)
    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)

    # تنظیم backtrader
    cerebro = bt.Cerebro()
    data_feed = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data_feed)
    cerebro.addstrategy(SimpleFibStrategy)
    cerebro.broker.setcash(10000)
    cerebro.broker.setcommission(commission=0.001)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.run()
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
