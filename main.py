# main.py
import argparse
from backtester import run_backtest
from telegram_bot import send_telegram_message

def main():
    parser = argparse.ArgumentParser(description="سیستم بک‌تست کریپتو روی KuCoin")
    parser.add_argument("--symbol", default="BTC/USDT", help="جفت ارز (مثال: BTC/USDT)")
    parser.add_argument("--timeframe", default="15m", help="تایم‌فریم (1m, 5m, 15m, 1h)")
    parser.add_argument("--since", default="2024-01-01", help="تاریخ شروع (YYYY-MM-DD)")
    parser.add_argument("--limit", type=int, default=1000, help="حداکثر کندل")
    
    args = parser.parse_args()
    
    print(f"در حال بک‌تست: {args.symbol} | تایم‌فریم: {args.timeframe} | از: {args.since}")
    
    signals = run_backtest(args.symbol, args.timeframe, args.since, args.limit)
    
    if signals:
        for sig in signals:
            msg = (
                f"🔔 <b>سیگنال خرید</b>\n"
                f"💰 ارز: {sig['symbol']}\n"
                f"📊 تایم‌فریم: {sig['timeframe']}\n"
                f"📌 قیمت: {sig['price']:.2f}\n"
                f"📅 زمان: {sig['datetime']}\n"
                f"🔄 سیستم: Vortex Volume Flow"
            )
            send_telegram_message(msg)
        print(f"{len(signals)} سیگنال یافت و ارسال شد.")
    else:
        print("هیچ سیگنالی یافت نشد.")

if __name__ == "__main__":
    main()
