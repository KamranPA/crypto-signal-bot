from data_fetcher import fetch_kucoin
from features import add_features
from backtester import Backtester
from telegram_bot import send_telegram_report
import pandas as pd

def main():
    results = []
    for symbol in ["BTC-USDT", "ETH-USDT", "SOL-USDT"]:
        print(f"دریافت داده: {symbol}")
        df = fetch_kucoin(symbol, "15min", 500)
        if df is None or len(df) < 100:
            continue
        df = add_features(df)
        backtester = Backtester(symbol, df)
        result = backtester.run()
        results.append(result)

    # ارسال گزارش
    send_telegram_report(results)
    print("✅ بک‌تست کامل شد و گزارش ارسال شد.")

if __name__ == "__main__":
    main()
