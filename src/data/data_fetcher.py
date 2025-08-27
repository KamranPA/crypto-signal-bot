# src/data/data_fetcher.py

import pandas as pd

def fetch_data(symbol, timeframe, start_date, end_date):
    """
    فرض: خروجی یک دیتافریم با ستون‌های ['open', 'high', 'low', 'close', 'volume', 'timestamp']
    مرتب شده از قدیم به جدید (صعودی بر اساس زمان)
    """
    # مثلاً از Binance API یا فایل CSV بخوانید
    df = pd.read_csv(f"data/{symbol}_{timeframe}.csv")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # فیلتر تاریخ
    df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
    
    return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
