import os
import pandas as pd
import numpy as np
from data_fetcher import fetch_kucoin
from features import add_features
from backtester import Backtester
from telegram_bot import send_telegram_report

def main():
    symbol_input = os.getenv("INPUT_SYMBOL", "BTC-USDT")
    timeframe = os.getenv("INPUT_TIMEFRAME", "15min")
    start_date = os.getenv("INPUT_START_DATE")
    end_date = os.getenv("INPUT_END_DATE")
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    if not start_date or not end_date:
        print('❌ لطفاً تاریخ شروع و پایان را وارد کنید.')
        return

    try:
        pd.to_datetime(start_date)
        pd.to_datetime(end_date)
    except Exception as e:
        print(f'❌ فرمت تاریخ نامعتبر است. فرمت صحیح: YYYY-MM-DD')
        return

    symbols = [s.strip() for s in symbol_input.split(",") if s.strip()]
    if not symbols:
        print('❌ هیچ ارزی وارد نشده است.')
        return

    print(f'📅 بک‌تست: {start_date} → {end_date}')
    print(f'⏱ تایم‌فریم: {timeframe}')
    print(f'🪙 ارزها: {symbols}')

    results = []
    for symbol in symbols:
        print(f'📥 دریافت داده: {symbol}')
        df = fetch_kucoin(symbol, timeframe, start_date, end_date)

        if df is None or len(df) < 50:
            print(f'⚠️ داده کافی برای {symbol} وجود ندارد.')
            continue

        if df.isna().any().any():
            print(f'⚠️ داده‌های {symbol} دارای nan هستند.')
            continue

        df = add_features(df)
        if len(df) < 10:
            print(f'⚠️ داده پس از پیش‌پردازش کافی نیست: {symbol}')
            continue

        if df.isna().any().any():
            print(f'⚠️ داده‌های {symbol} پس از افزودن ویژگی‌ها دارای nan است.')
            continue

        backtester = Backtester(symbol, df, capital=10000)
        result = backtester.run()
        results.append(result)

    if results and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        send_telegram_report(results, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
        print('✅ بک‌تست کامل شد و گزارش ارسال شد.')
    elif results:
        print('✅ بک‌تست کامل شد، اما ارسال تلگرام غیرفعال است.')
    else:
        print('❌ هیچ بک‌تستی انجام نشد.')

if __name__ == "__main__":
    main()
