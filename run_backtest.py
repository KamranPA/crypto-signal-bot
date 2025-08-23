# run_backtest.py
import os
from datetime import datetime, timedelta
from src.data.data_fetcher import fetch_ohlcv
from src.strategy.trading_system import generate_signal
from src.backtest.backtester import run_backtest
from src.utils.telegram_notifier import send_telegram_report

if __name__ == "__main__":
    symbol = os.getenv("SYMBOL", "BTC/USDT")
    timeframe = os.getenv("TIMEFRAME", "1h")
    days = int(os.getenv("DAYS", 30))

    since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

    print(f"🔍 دریافت داده از CoinEx: {symbol} | {timeframe} | {days} روز")
    df = fetch_ohlcv(symbol, timeframe, since)

    if df.empty:
        print("❌ داده‌ای دریافت نشد. نماد یا تایم فریم را بررسی کنید.")
        exit(1)

    print("📊 اجرای بک‌تست...")
    report = run_backtest(df, generate_signal)

    print("📨 ارسال گزارش به تلگرام...")
    send_telegram_report(report)

    print("✅ اجرا با موفقیت کامل شد.")
