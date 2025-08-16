# backtest.py
"""
بکتست با ورودی‌های دستی: ارز، تایم‌فریم، تاریخ
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
        # پیش‌فرض
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
    except Exception as e:
        print(f"❌ خطا در ارسال به تلگرام: {e}")

# --- استراتژی ---
class FibBOSFVGStrategy(bt.Strategy):
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

        fvg = detect_fvg(self.data_high, self.data_low, self.data_close)
        bos = detect_bos(self.data_high, self.data_low, lookback=50)

        if (current_price >= fib_71
                and bos == 'bearish'
                and fvg and fvg['type'] == 'bearish'):

            msg = (
                f"🔻 <b>سیگنال فروش (SHORT)</b>\n"
                f"📌 ارز: {config['symbol']}\n"
                f"⏱ تایم‌فریم: {config['timeframe']}\n"
                f"💰 قیمت: {current_price:.2f}\n"
                f"🎯 هدف: {recent_low:.2f}\n"
                f"🛑 حد ضرر: {recent_high * 1.01:.2f}"
            )
            print(msg)
            send_telegram(msg)
            self.order = self.sell()
            self.buy(exectype=bt.Order.Stop, price=recent_high * 1.01, size=1)
            self.sell(exectype=bt.Order.Limit, price=recent_low, size=1)

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
