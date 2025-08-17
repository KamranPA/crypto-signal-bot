# data_fetcher.py
import ccxt
import pandas as pd
from datetime import datetime

def fetch_kucoin_data(symbol, timeframe, since, limit=1000):
    exchange = ccxt.kucoin()
    
    # تبدیل تاریخ شروع به timestamp
    since_dt = datetime.strptime(since, "%Y-%m-%d")
    since_timestamp = int(since_dt.timestamp() * 1000)
    
    try:
        ohlcv = exchange.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            since=since_timestamp,
            limit=limit
        )
        
        if len(ohlcv) == 0:
            raise Exception("داده‌ای دریافت نشد.")
            
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
        
    except Exception as e:
        print(f"❌ خطای دریافت داده برای {symbol}: {e}")
        return pd.DataFrame()
