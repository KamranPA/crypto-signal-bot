# src/data/data_fetcher.py
import ccxt
import pandas as pd
import os

def fetch_ohlcv(symbol, timeframe, since, limit=1000):
    """
    دریافت داده OHLCV از صرافی CoinEx
    symbol: مثلاً 'BTC/USDT'
    timeframe: '15m', '30m', '1h'
    since: timestamp میلی‌ثانیه
    """
    exchange = ccxt.coinex({
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot'  # فقط اسپات (معمولاً پیش‌فرض است)
        }
    })

    # CoinEx نیاز به فرمت بدون اسلش دارد، ولی ccxt خودش تبدیل می‌کند
    try:
        ohlcv = exchange.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            since=since,
            limit=limit
        )
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except Exception as e:
        print(f"❌ خطای دریافت داده از CoinEx: {e}")
        raise
