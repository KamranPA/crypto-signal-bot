# data_fetcher.py
import ccxt
import pandas as pd
from datetime import datetime

def fetch_kucoin_data(symbol, timeframe, since, limit=1000):
    exchange = ccxt.kucoin()
    
    # تبدیل since به timestamp
    since_timestamp = int(datetime.strptime(since, "%Y-%m-%d").timestamp() * 1000)
    
    ohlcv = exchange.fetch_ohlcv(
        symbol=symbol,
        timeframe=timeframe,
        since=since_timestamp,
        limit=limit
    )
    
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df
