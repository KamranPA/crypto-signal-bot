# main.py
import argparse
import yaml
import os
from datetime import datetime
from backtester import run_backtest
from telegram_bot import send_telegram_message

def load_config(config_file="config.yml"):
    with open(config_file, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
        
    # جایگزینی متغیرهای محیطی مثل ${VAR}
    def resolve_env_vars(data):
        if isinstance(data, dict):
            return {k: resolve_env_vars(v) for k, v in data.items()}
        elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
            env_var = data[2:-1]
            return os.getenv(env_var, data)
        else:
            return data

    return resolve_env_vars(config)

def main():
    parser = argparse.ArgumentParser(description="سیستم بک‌تست کریپتو با تنظیمات YML")
    parser.add_argument("--config", default="config.yml", help="مسیر فایل تنظیمات")
    args = parser.parse_args()

    config = load_config(args.config)
    
    settings = config["settings"]
    date_range = config["date_range"]
    symbols = config["symbols"]
    timeframe = config["timeframe"]["main"]
    notifications = config["notifications"]["telegram"]
    strategy = config["strategy"]

    since = date_range["since"]
    limit = settings["limit"]

    print(f"🚀 شروع بک‌تست: از {since} | تایم‌فریم: {timeframe}")
    print(f"📊 ارزها: {', '.join(symbols)}")

    all_signals = []

    for symbol in symbols:
        try:
            signals = run_backtest(
                symbol=symbol,
                timeframe=timeframe,
                since=since,
                limit=limit
            )
            all_signals.extend(signals)
        except Exception as e:
            print(f"❌ خطا در {symbol}: {e}")

    # ارسال سیگنال‌ها به تلگرام
    if all_signals and notifications["enabled"]:
        for sig in all_signals:
            msg = (
                f"🔔 <b>سیگنال خرید</b>\n"
                f"💰 <b>ارز:</b> {sig['symbol']}\n"
                f"📊 <b>تایم‌فریم:</b> {sig['timeframe']}\n"
                f"📌 <b>قیمت:</b> {sig['price']}\n"
                f"📅 <b>زمان:</b> {sig['datetime']}\n"
                f"🔄 <b>استراتژی:</b> {strategy['name']}"
            )
            send_telegram_message(msg)
        print(f"✅ {len(all_signals)} سیگنال به تلگرام ارسال شد.")
    elif all_signals:
        print(f"📝 {len(all_signals)} سیگنال یافت شد (ارسال غیرفعال).")
    else:
        print("❌ هیچ سیگنالی یافت نشد.")

if __name__ == "__main__":
    main()
