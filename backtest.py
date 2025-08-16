# backtest.py
"""
Crypto Backtest Engine
استراتژی: Fib 71% + BOS + FVG
پشتیبانی از اجرای دستی با تنظیمات پویا در GitHub Actions
"""

import os
import sys
import json
import logging
import pandas as pd
import backtrader as bt

# تنظیم لاگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

# --- تنظیمات: استفاده از تنظیمات پویا یا پیش‌فرض ---
def load_config():
    """بارگذاری تنظیمات: اولویت با dynamic_settings.json"""
    dynamic_config = 'config/dynamic_settings.json'
    default_config = 'config/settings.json'

    if os.path.exists(dynamic_config):
        logger.info(f"🔄 استفاده از تنظیمات داینامیک: {dynamic_config}")
        with open(dynamic_config, 'r', encoding='utf-8') as f:
            return json.load(f)
    elif os.path.exists(default_config):
        logger.info(f"🔄 استفاده از تنظیمات پیش‌فرض: {default_config}")
        with open(default_config, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        logger.error("❌ هیچ فایل تنظیماتی پیدا نشد!")
        sys.exit(1)

config = load_config()

# --- ایجاد دایرکتوری‌های ضروری ---
os.makedirs('logs', exist_ok=True)
os.makedirs('data/cache', exist_ok=True)

# --- ایمپورت استراتژی ---
try:
    from strategies.FibBOSFVGStrategy import FibBOSFVGStrategy
except ImportError as e:
    logger.error(f"❌ خطای بارگذاری استراتژی: {e}")
    sys.exit(1)

# --- تابع: دریافت داده از بایننس ---
def fetch_binance_data(symbol, timeframe='15m', limit=500):
    """دریافت داده تاریخی از Binance"""
    import ccxt
    try:
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        logger.info(f"📥 دریافت داده: {symbol} | تایم‌فریم: {timeframe} | حداقل: {limit}")
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except Exception as e:
        logger.error(f"❌ خطا در دریافت داده {symbol}: {e}")
        return None

# --- اجرای اصلی ---
def run_backtest():
    logger.info("🚀 شروع بکتست...")

    # ایجاد موتور backtrader
    cerebro = bt.Cerebro()
    cerebro.addstrategy(FibBOSFVGStrategy,
                        fib_entry=config['fib_entry_level'],
                        fib_tp=config['fib_tp_level'],
                        fib_sl=config['fib_sl_level'],
                        lookback=config['lookback'],
                        enable_telegram=config.get('enable_telegram', True),
                        debug=config.get('debug', True))

    # تنظیمات بروکر
    cerebro.broker.setcash(10000)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% کارمزد
    cerebro.addsizer(bt.sizers.PercentSizer, percents=95)  # 95% سرمایه در هر معامله

    # افزودن داده‌ها
    data_loaded = False
    for symbol in config['symbols']:
        df = fetch_binance_data(symbol, config['timeframe'], config['lookback'] * 3)
        if df is not None and len(df) > config['lookback']:
            data_feed = bt.feeds.PandasData(dataname=df, name=symbol)
            cerebro.adddata(data_feed)
            data_loaded = True
            logger.info(f"✅ داده {symbol} با موفقیت بارگذاری شد.")
        else:
            logger.warning(f"⚠️ داده {symbol} در دسترس نیست یا حجم کم است.")

    if not data_loaded:
        logger.error("❌ هیچ داده‌ای بارگذاری نشد. بکتست لغو شد.")
        sys.exit(1)

    # --- اجرای بکتست ---
    logger.info(f"📊 شروع بکتست با {len(cerebro.datas)} دیتافید")
    logger.info(f"💵 سرمایه اولیه: ${cerebro.broker.getvalue():,.2f}")

    try:
        results = cerebro.run()
        final_value = cerebro.broker.getvalue()
        logger.info(f"✅ بکتست با موفقیت انجام شد.")
        logger.info(f"💼 سرمایه نهایی: ${final_value:,.2f}")
        logger.info(f"📈 سود/ضرر: {((final_value / 10000) - 1) * 100:.2f}%")

        # نمایش نمودار (در محیط‌های غیرسروری)
        if 'TERM' in os.environ or sys.platform != 'linux':
            cerebro.plot(style='candlestick', volume=False, figsize=(16, 9))

    except Exception as e:
        logger.error(f"❌ خطای اجرای بکتست: {e}")
        sys.exit(1)

# --- اجرای برنامه ---
if __name__ == '__main__':
    run_backtest()
