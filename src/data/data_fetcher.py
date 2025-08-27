# src/data/data_fetcher.py

import pandas as pd
import requests
from datetime import datetime

# نگاشت تایم‌فریم‌ها به فرمت CoinEx
TIMEFRAME_MAP = {
    '1m': '1m',
    '3m': '3m',
    '5m': '5m',
    '15m': '15m',
    '30m': '30m',
    '1h': '1H',
    '2h': '2H',
    '4h': '4H',
    '6h': '6H',
    '12h': '12H',
    '1d': '1D',
    '3d': '3D',
    '1w': '1W',
    '1M': '1M'
}

def fetch_data(symbol, timeframe, start_date, end_date):
    """
    دریافت داده کندلی از صرافی CoinEx
    """
    # تبدیل نماد: BTC/USDT → BTCUSDT
    market = symbol.replace("/", "").upper()
    
    # تبدیل تایم‌فریم به فرمت CoinEx
    if timeframe.lower() not in TIMEFRAME_MAP:
        print(f"❌ تایم‌فریم نامعتبر: {timeframe}")
        return pd.DataFrame()
    
    interval = TIMEFRAME_MAP[timeframe.lower()]
    
    # تبدیل تاریخ به ثانیه
    start_timestamp = int(pd.to_datetime(start_date).timestamp())
    end_timestamp = int(pd.to_datetime(end_date).timestamp())
    
    # URL API CoinEx
    url = "https://api.coinex.com/v1/market/kline"
    
    all_data = []
    current_start = start_timestamp
    
    while current_start < end_timestamp:
        params = {
            'market': market,
            'type': interval,
            'limit': 1000,
            'from': current_start,
            'to': min(current_start + 3600 * 24 * 30, end_timestamp)  # حداکثر 30 روز
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('code') != 0:
                error_msg = data.get('message', 'Unknown error')
                print(f"❌ خطای CoinEx: {error_msg}")
                return pd.DataFrame()
            
            klines = data['data']
            if not klines:
                break
            
            all_data.extend(klines)
            
            last_timestamp = klines[-1][0]
            if last_timestamp <= current_start:
                break
            current_start = last_timestamp + 1
        
        except Exception as e:
            print(f"❌ خطا در دریافت داده از CoinEx: {e}")
            return pd.DataFrame()
        
        time.sleep(0.1)  # جلوگیری از rate limit
    
    if not all_data:
        print(f"❌ داده‌ای برای {symbol} در تایم‌فریم {timeframe} یافت نشد.")
        return pd.DataFrame()
    
    df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'amount'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    df = df.set_index('timestamp')
    df = df.sort_index()
    
    df = df.loc[start_date:end_date]
    return df
