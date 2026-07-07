# مسیر فایل: data/yahoo_client.py
"""دریافت دیتای OHLCV بلندمدت از Yahoo Finance — فقط برای بخش تاریخی بک‌تست."""
from __future__ import annotations
import pandas as pd
import yfinance as yf


def fetch_ohlcv(symbol: str, period: str = "730d", interval: str = "1h") -> pd.DataFrame:
    """
    symbol مثل "BTC-USD".
    نکته: Yahoo برای interval='1h' معمولاً حداکثر ~۷۳۰ روز گذشته را می‌دهد.
    """
    ticker = yf.Ticker(symbol)
    raw = ticker.history(period=period, interval=interval)
    if raw.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume", "source"])

    df = raw.rename(columns={
        "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume",
    })[["open", "high", "low", "close", "volume"]]
    df.index = pd.to_datetime(df.index, utc=True)
    df.index.name = "timestamp"
    df["source"] = "yahoo"
    return df.sort_index()
