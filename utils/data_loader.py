# utils/data_loader.py
import ccxt
import pandas as pd
from datetime import datetime

def fetch_ohlcv(symbol, timeframe, since):
    exchange = ccxt.kucoin()  # می‌توانید به binance تغییر دهید
    since_ts = int(datetime.strptime(since, "%Y-%m-%d").timestamp() * 1000)
    
    data = exchange.fetch_ohlcv(symbol, timeframe, since=since_ts, limit=1000)
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # محاسبه ATR برای مدیریت ریسک
    df['tr0'] = df['high'] - df['low']
    df['tr1'] = abs(df['high'] - df['close'].shift(1))
    df['tr2'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
    df['atr'] = df['tr'].rolling(14).mean()
    
    return df.dropna()
