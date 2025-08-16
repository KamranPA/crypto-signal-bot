# utils/data_fetcher.py
import ccxt
import pandas as pd
import os

def fetch_binance_data(symbol, timeframe='15m', limit=500, cache=True):
    cache_file = f"data/cache/{symbol.replace('/', '_')}_{timeframe}.pkl"
    
    if cache and os.path.exists(cache_file):
        df = pd.read_pickle(cache_file)
        print(f"Loaded {symbol} from cache.")
        return df

    exchange = ccxt.binance()
    bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)

    if cache:
        os.makedirs('data/cache', exist_ok=True)
        df.to_pickle(cache_file)
        print(f"Saved {symbol} to cache.")

    return df
