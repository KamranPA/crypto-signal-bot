# src/data/data_fetcher.py
import ccxt
import pandas as pd

def fetch_ohlcv(symbol, timeframe, since, limit=1000):
    exchange = ccxt.coinex({
        'enableRateLimit': True
    })
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df
