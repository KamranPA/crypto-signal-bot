# src/data/data_fetcher.py

import pandas as pd
import os

def fetch_data(symbol, timeframe, start_date, end_date):
    # در عمل از صرافی داده بگیرید
    file_path = f"data/{symbol}_{timeframe}.csv"
    if not os.path.exists(file_path):
        return pd.DataFrame()
    
    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp')
    df = df.sort_index()
    return df.loc[start_date:end_date]
