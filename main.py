import os
import pandas as pd
import numpy as np
from data_fetcher import fetch_kucoin
from features import add_features
from backtester import Backtester
from telegram_bot import send_telegram_report

def main():
    # دریافت ورودی‌ها از محیط (GitHub Actions)
    symbol_input = os.getenv("INPUT_SYMBOL", "BTC-USDT")
    timeframe = os.getenv("INPUT_TIMEFRAME", "15min")
    start_date = os.getenv("INPUT_START_DATE")
    end_date = os.getenv("INPUT_END_DATE")
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    # بررسی ورودی تاریخ
    if not start_date or not end_date:
        print('❌ لطفاً تاریخ شروع و پایان را وارد کنید.')
        return

    # اعتبارسنجی فرمت تاریخ
    try:
        pd.to_datetime(start_date)
        pd.to_datetime(end_date)
    except Exception as e:
        print(f'❌ فرمت تاریخ نامعتبر است. فرمت صحیح: YYYY-MM-DD')
        return

    # پردازش لیست ارزها
    symbols = [s.strip() for s in symbol_input.split(",") if s.strip()]
    if not symbols:
        print('❌ هیچ ارزی وارد نشده است.')
        return

    # نمایش اطلاعات اجرا
    print(f'📅 بک‌تست: {start_date} → {end_date}')
    print(f'⏱ تایم‌فریم: {timeframe}')
    print(f'🪙 ارزها: {symbols}')

    # لیست نتایج
    results = []

    # پردازش هر ارز
    for symbol in symbols:
        print(f'📥 دریافت داده: {symbol}')
        df = fetch_kucoin(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date
        )

        # بررسی داده
        if df is None or len(df) < 50:
            print(f'⚠️ داده کافی برای {symbol} وجود ندارد.')
            continue

        # افزودن ویژگی‌ها
        df = add_features(df)
        if len(df) < 10:
            print(f'⚠️ داده پس از پیش‌پردازش کافی نیست: {symbol}')
            continue

        # اجرای بک‌تست
        backtester = Backtester(symbol, df, capital=10000)
        result = backtester.run()
        results.append(result)

    # ارسال گزارش به تلگرام (اگر توکن وجود داشته باشد)
    if results and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        send_telegram_report(results, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
        print('✅ بک‌تست کامل شد و گزارش ارسال شد.')
    elif results:
        print('✅ بک‌تست کامل شد، اما ارسال تلگرام غیرفعال است (توکن یا چت آی‌دی ندارید)')
    else:
        print('❌ هیچ بک‌تستی انجام نشد.')

# اجرای برنامه
if __name__ == "__main__":
    main()
