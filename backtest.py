# backtest.py
"""
Crypto Backtest Engine - نسخه نهایی با پشتیبانی از KuCoin و تاریخ
"""

import os
import sys
import json
import logging
import pandas as pd
import backtrader as bt
from datetime import datetime
import pytz

# تنظیم لاگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

# --- بارگذاری تنظیمات ---
def load_config():
    dynamic = 'config/dynamic_settings.json'
    default = 'config/settings.json'
    if os.path.exists(dynamic):
        logger.info("🔄 استفاده از تنظیمات داینامیک")
        with open(dynamic, 'r', encoding='utf-8') as f:
            return json.load(f)
    elif os.path.exists(default):
        logger.info("🔄 استفاده از تنظیمات پیش‌فرض")
        with open(default, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        logger.error("❌ فایل تنظیمات یافت نشد!")
        sys.exit(1)

config = load_config()

# --- ایجاد دایرکتوری‌ها ---
os.makedirs('logs', exist_ok=True)
os.makedirs('data/cache', exist_ok=True)

# --- تبدیل تاریخ به میلی‌ثانیه ---
def date_to_milliseconds(date_str):
    """تبدیل 'YYYY-MM-DD' به میلی‌ثانیه"""
    if not date_str:
        logger.error("❌ تاریخ ورودی خالی است.")
        sys.exit(1)
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        dt = pytz.UTC.localize(dt)
        return int(dt.timestamp() * 1000)
    except ValueError as e:
        logger.error(f"❌ فرمت تاریخ نادرست است '{date_str}': {e}")
        sys.exit(1)

# --- دریافت داده از KuCoin ---
def fetch_kucoin_data(symbol, timeframe, start_date, end_date=None):
    import ccxt
    try:
        exchange = ccxt.kucoin({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'
            }
        })
        exchange.load_markets()

        # بررسی تاریخ‌ها و تنظیم پیش‌فرض
        start_date = config.get('start_date', '2024-01-01')
        end_date = config.get('end_date', '2024-06-01')

        # تبدیل / به - برای سازگاری
        start_date = start_date.replace('/', '-')
        end_date = end_date.replace('/', '-')

        # بررسی فرمت تاریخ
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError as e:
            logger.error(f"❌ فرمت تاریخ نادرست است: {start_date} یا {end_date}")
            sys.exit(1)

        since = date_to_milliseconds(start_date)
        until = date_to_milliseconds(end_date)

        all_bars = []
        limit = 1000  # حداکثر کندل در هر درخواست
        current = since

        logger.info(f"📥 دانلود داده: {symbol} | {start_date} → {end_date} | تایم‌فریم: {timeframe}")

        while current < until:
            try:
                bars = exchange.fetch_ohlcv(symbol, timeframe, since=current, limit=limit)
                if not bars:
                    break

                # فیلتر کندل‌های قبل از until
                valid_bars = [bar for bar in bars if bar[0] < until]
                all_bars.extend(valid_bars)

                # به‌روزرسانی current برای درخواست بعدی
                current = bars[-1][0] + 1

                if len(bars) < limit:
                    break  # داده تمام شده

            except Exception as e:
                logger.warning(f"⚠️ خطا در دریافت داده از KuCoin: {e}")
                break

        if not all_bars:
            logger.error("❌ هیچ داده‌ای دریافت نشد.")
            return None

        df = pd.DataFrame(all_bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df.set_index('timestamp', inplace=True)

        # فیلتر بر اساس بازه دقیق
        df = df.loc[start_date:end_date]
        logger.info(f"✅ {len(df)} کندل دریافت شد برای {symbol}")
        return df

    except Exception as e:
        logger.error(f"❌ خطا در ارتباط با KuCoin: {e}")
        return None

# --- ایمپورت استراتژی ---
try:
    from strategies.FibBOSFVGStrategy import FibBOSFVGStrategy
except Exception as e:
    logger.error(f"❌ خطای ایمپورت استراتژی: {e}")
    sys.exit(1)

# --- اجرای اصلی ---
def run_backtest():
    logger.info("🚀 شروع بکتست با بازه زمانی مشخص و KuCoin")

    cerebro = bt.Cerebro()
    cerebro.addstrategy(FibBOSFVGStrategy,
                        fib_entry=config['fib_entry_level'],
                        fib_tp=config['fib_tp_level'],
                        fib_sl=config['fib_sl_level'],
                        debug=config.get('debug', True))

    cerebro.broker.setcash(10000)
    cerebro.broker.setcommission(commission=0.001)
    cerebro.addsizer(bt.sizers.PercentSizer, percents=95)

    # افزودن داده‌ها
    data_loaded = False
    for symbol in config['symbols']:
        df = fetch_kucoin_data(
            symbol=symbol,
            timeframe=config['timeframe'],
            start_date=None,  # از config استفاده می‌کند
            end_date=None
        )
        if df is not None and len(df) > 10:
            data_feed = bt.feeds.PandasData(dataname=df, name=symbol)
            cerebro.adddata(data_feed)
            data_loaded = True
            logger.info(f"✅ داده {symbol} با موفقیت بارگذاری شد.")
        else:
            logger.warning(f"⚠️ داده {symbol} در بازه موردنظر یافت نشد.")

    if not data_loaded:
        logger.error("❌ هیچ داده‌ای بارگذاری نشد.")
        sys.exit(1)

    # اجرای بکتست
    logger.info(f"📊 شروع بکتست با سرمایه اولیه: $10,000")
    try:
        results = cerebro.run()
        final_value = cerebro.broker.getvalue()
        profit = ((final_value / 10000) - 1) * 100
        logger.info(f"💼 سرمایه نهایی: ${final_value:,.2f}")
        logger.info(f"📈 سود/ضرر: {profit:+.2f}%")

        if 'TERM' in os.environ or sys.platform != 'linux':
            cerebro.plot(style='candlestick', volume=False, figsize=(16, 9))

    except Exception as e:
        logger.error(f"❌ خطا در اجرای بکتست: {e}")
        sys.exit(1)

# --- اجرای برنامه ---
if __name__ == '__main__':
    run_backtest()
