# backtest.py
"""
استراتژی معاملاتی دوطرفه بر اساس:
- BOS → Pullback → Fib 71% + FVG → ورود در جهت روند
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

# --- تابع یافتن آخرین HL و LL ---
def find_last_high_low(data, kind='high', lookback=50):
    """یافتن آخرین سقف (HL) یا کف (LL)"""
    values = list(data.get(-lookback, lookback))
    if len(values) < 3:
        return None, None

    for i in range(2, len(values)-2):
        if kind == 'high' and values[i] > values[i-1] and values[i] > values[i+1]:
            return values[i], i
        elif kind == 'low' and values[i] < values[i-1] and values[i] < values[i+1]:
            return values[i], i
    return None, None

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

# --- استراتژی دوطرفه ---
class FibBOSFVGStrategy(bt.Strategy):
    params = (
        ('print_log', True),
    )

    def __init__(self):
        self.data_close = self.datas[0].close
        self.data_high = self.datas[0].high
        self.data_low = self.datas[0].low
        self.order = None

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
            elif order.issell():
                self.log(f"SELL EXECUTED, Price: {order.executed.price:.2f}")

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        if trade.pnlcomm < 0:
            self.sl_hits += 1
            self.log("✅ حد ضرر فعال شد (SL)")
        else:
            self.tp_hits += 1
            self.log("✅ حد سود فعال شد (TP)")

    def next(self):
        if self.order:
            return
        if len(self) < 100:
            return

        # --- 1. تشخیص BOS نزولی (شکست HL) ---
        recent_lows = list(self.data_low.get(-50, 50))
        bos_bearish = False
        for i in range(-5, -2):
            if i >= -len(recent_lows): continue
            # تشخیص HL (Higher Low)
            if recent_lows[i] > recent_lows[i-1] and recent_lows[i] > recent_lows[i+1]:
                if self.data_high[0] < recent_lows[i]:
                    bos_bearish = True
                    break

        # --- 2. تشخیص BOS صعودی (شکست LH) ---
        recent_highs = list(self.data_high.get(-50, 50))
        bos_bullish = False
        for i in range(-5, -2):
            if i >= -len(recent_highs): continue
            # تشخیص LH (Lower High)
            if recent_highs[i] < recent_highs[i-1] and recent_highs[i] < recent_highs[i+1]:
                if self.data_low[0] > recent_highs[i]:
                    bos_bullish = True
                    break

        current_price = self.data_close[0]

        # --- ورود شورت در روند نزولی ---
        if bos_bearish:
            hl, _ = find_last_high_low(self.data_high, kind='high', lookback=30)
            ll, _ = find_last_high_low(self.data_low, kind='low', lookback=30)
            if hl and ll and hl > ll:
                # فیبوناچی از HL به LL
                diff = hl - ll
                fib_71 = ll + 0.71 * diff
                fib_618 = ll + 0.618 * diff
                fib_886 = ll + 0.886 * diff

                # بررسی FVG نزولی در ناحیه 0.618 تا 0.886
                fvg = detect_fvg(self.data_high, self.data_low, self.data_close)
                if fvg and fvg['type'] == 'bearish' and fib_618 <= fvg['mid'] <= fib_886:
                    if abs(current_price - fib_71) / fib_71 < 0.001:
                        self.total_signals += 1
                        self.log(f"🔻 SHORT ENTRY at {current_price}")
                        self.order = self.sell()
                        self.buy(exectype=bt.Order.Stop, price=hl * 1.01, size=1)  # SL بالاتر از HL
                        self.sell(exectype=bt.Order.Limit, price=ll, size=1)       # TP در LL

        # --- ورود لانگ در روند صعودی ---
        elif bos_bullish:
            lh, _ = find_last_high_low(self.data_low, kind='low', lookback=30)
            hh, _ = find_last_high_low(self.data_high, kind='high', lookback=30)
            if lh and hh and hh > lh:
                # فیبوناچی از LH به HH
                diff = hh - lh
                fib_71 = hh - 0.71 * diff
                fib_618 = hh - 0.618 * diff
                fib_886 = hh - 0.886 * diff

                # بررسی FVG صعودی در ناحیه 0.618 تا 0.886
                fvg = detect_fvg(self.data_high, self.data_low, self.data_close)
                if fvg and fvg['type'] == 'bullish' and fib_618 <= fvg['mid'] <= fib_886:
                    if abs(current_price - fib_71) / fib_71 < 0.001:
                        self.total_signals += 1
                        self.log(f"🟢 LONG ENTRY at {current_price}")
                        self.order = self.buy()
                        self.sell(exectype=bt.Order.Stop, price=lh * 0.99, size=1)  # SL پایین‌تر از LH
                        self.buy(exectype=bt.Order.Limit, price=hh, size=1)        # TP در HH

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
