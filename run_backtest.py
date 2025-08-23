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

    print(f"Fetching data for {symbol} on {timeframe}, {days} days...")
    df = fetch_ohlcv(symbol, timeframe, since)

    print("Running backtest...")
    report = run_backtest(df, generate_signal)

    print("Sending report to Telegram...")
    send_telegram_report(report)

    print("✅ Done.")
