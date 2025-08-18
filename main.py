import os
import pandas as pd
from data_fetcher import fetch_kucoin
from features import add_features
from backtester import Backtester
from telegram_bot import send_telegram_report

def main():
    # دریافت ورودی‌ها
    symbol_input = os.getenv("INPUT_SYMBOL", "BTC-USDT")
    timeframe = os.getenv("INPUT_TIMEFRAME", "15min")
    start_date = os.getenv("INPUT_START_DATE")
    end_date = os.getenv("INPUT_END_DATE")

    if not start_date or not end_date:
        print("❌ لطفاً تاریخ شروع و پایان را وارد کنید.")
        return

    # اعتبارسنجی تاریخ
    try:
        pd.to_datetime(start_date)
        pd.to_datetime(end_date)
    except:
        print("❌ فرمت تاریخ نامعتبر است. فرمت صحیح: YYYY-MM-DD")
        return

    symbols = [s.strip() for s in symbol_input.split(",") if s.strip()]
    if not symbols:
        print("❌ هیچ ارزی وارد نشده است.")
        return

    print(f"📅 بک‌تست: {start_date} → {end_date}")
    print(f"⏱ تایم‌فریم: {timeframe}")
    print(f"🪙 ارزها: {symbols}")

    results = []
    for symbol in symbols:
        print(f"📥 دریافت داده: {symbol}")
        df = fetch_kucoin(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date
        )
        if df is None or len(df) < 10:
            print(f"⚠️ داده کافی برای {symbol} وجود ندارد.")
            continue

        df = add_features(df)
        backtester = Backtester(symbol, df)
        result = backtester.run()
        results.append(result)

    # ارسال گزارش
    if results:
        send_telegram_report(results)
        print("✅ بک‌تست کامل شد و گزارش ارسال شد.")
    else:
        print("❌ هیچ بک‌تستی انجام نشد.")

if __name__ == "__main__":
    main()
