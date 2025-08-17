# main.py
import argparse
import yaml
import os
from datetime import datetime
from backtester import run_backtest
from telegram_bot import send_telegram_message

def load_config(config_file="config.yml"):
    with open(config_file, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

def main():
    parser = argparse.ArgumentParser(description="اجرای سیستم بک‌تست با تنظیمات YML")
    parser.add_argument("--config", default="config.yml", help="مسیر فایل تنظیمات YML")
    args = parser.parse_args()

    config = load_config(args.config)

    settings = config["settings"]
    date_range = config["date_range"]
    symbols = config["symbols"]
    timeframe = config["timeframe"]["main"]
    notifications = config["notifications"]
    strategy = config["strategy"]

    # تبدیل since به timestamp
    since_str = date_range["since"]
    since = int(datetime.strptime(since_str, "%Y-%m-%d").timestamp() * 1000)
    until = date_range.get("until")

    print(f"🚀 شروع بک‌تست: {since_str} تا {until or 'حال'} | تایم‌فریم: {timeframe}")

    all_signals = []

    for symbol in symbols:
        print(f"\n🔍 در حال تحلیل: {symbol}")
        try:
            signals = run_backtest(
                symbol=symbol,
                timeframe=timeframe,
                since=since_str,
                limit=settings["limit"]
            )
            all_signals.extend(signals)
        except Exception as e:
            print(f"❌ خطا در تحلیل {symbol}: {e}")

    # ارسال سیگنال‌ها
    if all_signals and notifications["telegram"]["enabled"]:
        for sig in all_signals:
            msg = (
                f"🔔 <b>سیگنال خرید</b>\n"
                f"💰 ارز: {sig['symbol']}\n"
                f"📊 تایم‌فریم: {sig['timeframe']}\n"
                f"📌 قیمت: {sig['price']:.2f}\n"
                f"📅 زمان: {sig['datetime']}\n"
                f"🔄 استراتژی: {strategy['name']}"
            )
            send_telegram_message(msg)
        print(f"✅ {len(all_signals)} سیگنال به تلگرام ارسال شد.")
    else:
        print("❌ سیگنالی یافت نشد.")

if __name__ == "__main__":
    main()
