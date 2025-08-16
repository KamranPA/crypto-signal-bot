# backtest.py
"""
بکتست با گزارش‌گیری کامل: تعداد سیگنال، SL، TP
"""

import ccxt
import pandas as pd
import backtrader as bt
import requests
import os
import json
from datetime import datetime
import pytz

# --- بارگذاری تنظیمات ---
def load_config():
    if os.path.exists('config/dynamic_settings.json'):
        with open('config/dynamic_settings.json', 'r') as f:
            return json.load(f)
    else:
        return {
            "symbol": "BTC/USDT",
            "timeframe": "15m",
            "start_date": "2024-01-01",
            "end_date": "2024-06-01"
        }

config = load_config()

# --- تبدیل تاریخ به میلی‌ثانیه ---
def date_to_milliseconds(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    dt = pytz.UTC.localize(dt)
    return int(dt.timestamp() * 1000)

# --- ایمپورت توابع ---
from utils.detect_fvg import detect_fvg
from utils.detect_bos import detect_bos

# --- تابع ارسال به تلگرام ---
def send_telegram(message):
    try:
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        if not token or not chat_id:
            print("⚠️ هشدار: توکن یا chat_id تنظیم نشده — ارسال تلگرام ناموفق")
            return
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        requests.post(url, data=payload, timeout=10)
        print("✅ سیگنال به تلگرام ارسال شد")
    except Exception as e:
        print(f"❌ خطا در ارسال به تلگرام: {e}")

# --- استراتژی با گزارش‌گیری ---
class FibBOSFVGStrategy(bt.Strategy):
    params = (
        ('print_log', True),
    )

    def __init__(self):
        self.data_close = self.datas[0].close
        self.data_high = self.datas[0].high
        self.data_low = self.datas[0].low
        self.order = None
        self.buy_price = None

        # متغیرهای گزارش
        self.total_signals = 0
        self.sl_hits = 0
        self.tp_hits = 0

    def log(self, txt, debug=False):
        if self.params.print_log or debug:
            print(f"{self.datas[0].datetime.datetime(0)} | {txt}")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f"BUY EXECUTED, Price: {order.executed.price:.2f}")
                self.buy_price = order.executed.price
            elif order.issell():
                self.log(f"SELL EXECUTED, Price: {order.executed.price:.2f}")
                self.buy_price = None

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        profit = trade.pnlcomm
        self.log(f"OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {profit:.2f}")

        # تشخیص نوع بسته شدن
        if self.buy_price:
            if trade.exitprice < self.buy_price:
                self.sl_hits += 1
                self.log("✅ حد ضرر فعال شد (SL)")
            else:
                self.tp_hits += 1
                self.log("✅ حد سود فعال شد (TP)")
        else:
            if trade.exitprice > self.buy_price:
                self.sl_hits += 1
                self.log("✅ حد ضرر فعال شد (SL)")
            else:
                self.tp_hits += 1
                self.log("✅ حد سود فعال شد (TP)")

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

        fvg = detect_fvg(self.data_high, self.data_low, self.data_close)
        bos = detect_bos(self.data_high, self.data_low, lookback=50)

        # ورود شورت
        if (current_price >= fib_71
                and bos == 'bearish'
                and fvg and fvg['type'] == 'bearish'):

            self.total_signals += 1
            self.log(f"🔻 SHORT ENTRY at {current_price}")
            self.order = self.sell()
            self.buy(exectype=bt.Order.Stop, price=recent_high * 1.01, size=1)  # SL
            self.sell(exectype=bt.Order.Limit, price=recent_low, size=1)        # TP

    def stop(self):
        print("\n==================== گزارش نهایی ====================")
        print(f"📌 ارز: {config['symbol']}")
        print(f"⏱ تایم‌فریم: {config['timeframe']}")
        print(f"📅 بازه: {config['start_date']} → {config['end_date']}")
        print(f"📊 تعداد سیگنال‌ها: {self.total_signals}")
        print(f"🛑 تعداد حد ضرر (SL): {self.sl_hits}")
        print(f"🎯 تعداد حد سود (TP): {self.tp_hits}")
        print(f"💼 سود/ضرر نهایی: {self.broker.getvalue():.2f}")

        # ارسال گزارش به تلگرام
        msg = (
            f"📊 <b>گزارش بکتست</b>\n"
            f"📌 ارز: {config['symbol']}\n"
            f"⏱ تایم‌فریم: {config['timeframe']}\n"
            f"📅 بازه: {config['start_date']} → {config['end_date']}\n"
            f"🔍 تعداد سیگنال: {self.total_signals}\n"
            f"🛑 حد ضرر: {self.sl_hits}\n"
            f"🎯 حد سود: {self.tp_hits}\n"
            f"💼 سرمایه نهایی: ${self.broker.getvalue():.2f}"
        )
        send_telegram(msg)

# --- دریافت داده با بازه زمانی ---
def fetch_data(symbol, timeframe, start_date, end_date):
    exchange = ccxt.kucoin({'enableRateLimit': True})
    since = date_to_milliseconds(start_date)
    until = date_to_milliseconds(end_date)
    all_bars = []
    limit = 1000
    current = since

    while current < until and len(all_bars) < 1000:
        bars = exchange.fetch_ohlcv(symbol, timeframe, since=current, limit=limit)
        if not bars:
            break
        valid_bars = [bar for bar in bars if bar[0] < until]
        all_bars.extend(valid_bars)
        current = bars[-1][0] + 1
        if len(bars) < limit:
            break

    df = pd.DataFrame(all_bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

# --- اجرای بکتست ---
if __name__ == '__main__':
    print(f"🔄 دریافت داده: {config['symbol']} | {config['timeframe']} | {config['start_date']} → {config['end_date']}")
    try:
        df = fetch_data(config['symbol'], config['timeframe'], config['start_date'], config['end_date'])
        print(f"✅ {len(df)} کندل دریافت شد")
    except Exception as e:
        print(f"❌ خطا در دریافت داده: {e}")
        df = pd.DataFrame()

    if len(df) > 70:
        cerebro = bt.Cerebro()
        data_feed = bt.feeds.PandasData(dataname=df)
        cerebro.adddata(data_feed)
        cerebro.addstrategy(FibBOSFVGStrategy)
        cerebro.broker.setcash(10000)
        cerebro.broker.setcommission(commission=0.001)

        print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
        cerebro.run()
        print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    else:
        print("❌ داده کافی برای بکتست وجود ندارد")
