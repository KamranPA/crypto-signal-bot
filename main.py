# main.py
import argparse
from backtester import run_backtest
from telegram_bot import send_telegram_message

def main():
    parser = argparse.ArgumentParser(description="بک‌تست دستی کریپتو با تنظیمات قابل تنظیم")

    # آرگومان‌های دستی
    parser.add_argument("--symbol", required=True, help="جفت ارز: مثلاً BTC/USDT")
    parser.add_argument("--timeframe", default="15m", help="تایم‌فریم: 1m, 5m, 15m, 1h")
    parser.add_argument("--since", required=True, help="تاریخ شروع: YYYY-MM-DD")
    parser.add_argument("--until", default=None, help="تاریخ پایان: YYYY-MM-DD (اختیاری)")
    parser.add_argument("--limit", type=int, default=1000, help="حداکثر کندل")

    args = parser.parse_args()

    print(f"🔍 بک‌تست: {args.symbol} | {args.timeframe} | از {args.since} تا {args.until or 'آخر'}")

    try:
        signals = run_backtest(
            symbol=args.symbol,
            timeframe=args.timeframe,
            since=args.since,
            until=args.until,
            limit=args.limit
        )

        if signals:
            for sig in signals:
                msg = (
                    f"🔔 <b>سیگنال خرید</b>\n"
                    f"💰 ارز: {sig['symbol']}\n"
                    f"📊 تایم‌فریم: {sig['timeframe']}\n"
                    f"📌 قیمت: {sig['price']}\n"
                    f"📅 زمان: {sig['datetime']}"
                )
                print(f"✅ سیگنال: {sig['symbol']} در {sig['datetime']} — {sig['price']}")
                send_telegram_message(msg)
            print(f"📤 {len(signals)} سیگنال به تلگرام ارسال شد.")
        else:
            print("❌ سیگنالی یافت نشد.")

    except Exception as e:
        print(f"❌ خطای سیستم: {e}")

if __name__ == "__main__":
    main()
