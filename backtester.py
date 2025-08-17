# backtester.py
import pandas as pd
from data_fetcher import fetch_kucoin_data

def generate_signals(df):
    df = df.copy()
    
    # محاسبه EMA
    df['ema8'] = df['close'].ewm(span=8).mean()
    df['ema21'] = df['close'].ewm(span=21).mean()
    
    # حجم نسبی
    df['vol_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
    
    # شرایط خرید
    long_condition = (
        (df['low'] < df['low'].shift(1).rolling(5).min()) &  # wick پایینی (لیکوییدیتی هانت)
        (df['close'] > df['open']) &                         # کندل صعودی
        (df['vol_ratio'] > 1.5) &                           # حجم بالا
        (df['close'] > df['ema8']) &                        # بالای EMA8
        (df['ema8'] > df['ema21'])                          # EMA8 بالای EMA21
    )
    
    df['signal'] = 0
    df.loc[long_condition, 'signal'] = 1  # 1 = خرید
    
    return df

def run_backtest(symbol, timeframe, since, limit):
    df = fetch_kucoin_data(symbol, timeframe, since, limit)
    df = generate_signals(df)
    
    # فیلتر سیگنال‌های فعال
    signals = df[df['signal'] == 1]
    
    results = []
    for _, row in signals.iterrows():
        results.append({
            "symbol": symbol,
            "timeframe": timeframe,
            "type": "BUY",
            "price": row['close'],
            "datetime": row['datetime'].strftime("%Y-%m-%d %H:%M")
        })
    
    return results
