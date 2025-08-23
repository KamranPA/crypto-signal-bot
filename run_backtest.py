# run_backtest.py
import os
from datetime import datetime, timedelta
from src.data.data_fetcher import fetch_ohlcv
from src.strategy.trading_system import generate_signal
from src.backtest.backtester import run_backtest
from src.utils.telegram_notifier import send_telegram_report

def date_to_milliseconds(date_str):
    """تبدیل تاریخ به میلی‌ثانیه"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return int(dt.timestamp() * 1000)

if __name__ == "__main__":
    symbol = os.getenv("SYMBOL", "BTC/USDT")
    timeframe = os.getenv("TIMEFRAME", "1h")
    start_date = os.getenv("START_DATE", "2024-01-01")
    end_date = os.getenv("END_DATE", "2024-03-01")

    since = date_to_milliseconds(start_date)
    until = date_to_milliseconds(end_date)

    print(f"🔍 دریافت داده از {start_date} تا {end_date} | نماد: {symbol} | تایم فریم: {timeframe}")
    df = fetch_ohlcv(symbol, timeframe, since, limit=1000)

    # فیلتر تا تاریخ پایان
    df = df[df.index <= datetime.strptime(end_date, "%Y-%m-%d")]

    if df.empty:
        print("❌ داده‌ای دریافت نشد. نماد یا بازه زمانی را بررسی کنید.")
        exit(1)

    print("📊 اجرای بک‌تست...")
    report = run_backtest(df, generate_signal)

    # اضافه کردن بازه زمانی به گزارش
    report['start_date'] = start_date
    report['end_date'] = end_date

    print("📨 ارسال گزارش به تلگرام...")
    send_telegram_report(report)

    print("✅ اجرا با موفقیت کامل شد.")
