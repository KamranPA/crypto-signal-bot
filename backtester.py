# backtester.py
import pandas as pd
from data_fetcher import fetch_kucoin_data

def generate_signals(df, ema_fast=8, ema_slow=21, vol_ratio_threshold=1.5):
    df = df.copy()
    
    # محاسبه EMA
    df['ema8'] = df['close'].ewm(span=ema_fast).mean()
    df['ema21'] = df['close'].ewm(span=ema_slow).mean()
    
    # حجم نسبی
    df['vol_ma'] = df['volume'].rolling(20).mean()
    df['vol_ratio'] = df['volume'] / df['vol_ma']
    
    # شناسایی wick پایینی (لیکوییدیتی هانت)
    lower_wick = df['low'] < df['low'].shift(1).rolling(5).min().shift(-1)
    
    # شرط خرید
    long_condition = (
        lower_wick &
        (df['close'] > df['open']) &
        (df['vol_ratio'] > vol_ratio_threshold) &
        (df['close'] > df['ema8']) &
        (df['ema8'] > df['ema21'])
    )
    
    df['signal'] = 0
    df.loc[long_condition, 'signal'] = 1
    
    return df

def run_backtest(symbol, timeframe, since, limit):
    df = fetch_kucoin_data(symbol, timeframe, since, limit)
    
    if df.empty or len(df) < 50:
        return []
    
    df = generate_signals(df)
    signals = df[df['signal'] == 1]
    
    results = []
    for _, row in signals.iterrows():
        results.append({
            "symbol": symbol,
            "timeframe": timeframe,
            "type": "BUY",
            "price": round(row['close'], 6),
            "datetime": row['datetime'].strftime("%Y-%m-%d %H:%M")
        })
    
    return results
