# data_fetcher.py
import pandas as pd
import requests
import time
from datetime import datetime
import ccxt

def fetch_kucoin(symbol, timeframe, start_date, end_date):
    """
    دریافت داده کندل‌های تاریخی از صرافی KuCoin
    """
    exchange = ccxt.kucoin()

    try:
        since = exchange.parse8601(f"{start_date}T00:00:00Z")
        limit = 1000  # حداکثر تعداد کندل در هر درخواست
        all_ohlcv = []

        while since < exchange.parse8601(f"{end_date}T00:00:00Z"):
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
            if not ohlcv:
                break
            all_ohlcv.extend(ohlcv)
            since = ohlcv[-1][0] + 1
            time.sleep(exchange.rateLimit / 1000)

        if not all_ohlcv:
            print(f"❌ داده‌ای برای {symbol} یافت نشد.")
            return None

        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)

        # فیلتر تاریخ
        df = df[(df.index >= start_date) & (df.index <= end_date)]

        if df.empty:
            print(f"❌ داده‌ای در بازه زمانی برای {symbol} وجود ندارد.")
            return None

        return df

    except Exception as e:
        print(f"❌ خطا در دریافت داده از KuCoin: {e}")
        return None
