# backtest.py
import backtrader as bt
import os
import json
from utils.data_fetcher import fetch_binance_data
from strategies.FibBOSFVGStrategy import FibBOSFVGStrategy

# بارگذاری تنظیمات
with open('config/settings.json') as f:
    config = json.load(f)

# ایجاد دایرکتوری لاگ
os.makedirs('logs', exist_ok=True)

# اجرای بکتست
cerebro = bt.Cerebro()
cerebro.addstrategy(FibBOSFVGStrategy, **config)

for symbol in config['symbols']:
    df = fetch_binance_data(symbol, config['timeframe'], config['lookback'] * 2)
    data = bt.feeds.PandasData(dataname=df, name=symbol)
    cerebro.adddata(data)

cerebro.broker.setcash(10000)
cerebro.broker.setcommission(commission=0.001)
cerebro.addsizer(bt.sizers.FixedSize, stake=1)

print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
cerebro.run()
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

cerebro.plot(style='candlestick')
