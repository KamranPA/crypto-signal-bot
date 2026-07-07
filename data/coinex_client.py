# مسیر فایل: data/coinex_client.py
"""دریافت دیتای OHLCV از CoinEx از طریق ccxt — منبع اصلی برای اجرای زنده."""
from __future__ import annotations
import time
import pandas as pd
import ccxt


def get_exchange() -> ccxt.coinex:
    return ccxt.coinex({"enableRateLimit": True})


def fetch_ohlcv(symbol: str, timeframe: str = "1h", since_ms: int | None = None,
                 limit: int = 1000) -> pd.DataFrame:
    """
    symbol مثل "BTC/USDT". خروجی: DataFrame با ایندکس زمانی UTC و ستون‌های
    open/high/low/close/volume، مرتب صعودی.
    """
    exchange = get_exchange()
    all_rows = []
    fetch_since = since_ms

    while True:
        batch = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=fetch_since, limit=limit)
        if not batch:
            break
        all_rows.extend(batch)
        if len(batch) < limit:
            break
        fetch_since = batch[-1][0] + 1
        time.sleep(exchange.rateLimit / 1000)

    df = pd.DataFrame(all_rows, columns=["ts", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df = df.set_index("timestamp").drop(columns=["ts"])
    df["source"] = "coinex"
    return df.sort_index()


def fetch_latest_candle(symbol: str, timeframe: str = "1h") -> pd.DataFrame:
    """برای job ساعتی: فقط چند کندل آخر (کافی برای محاسبه‌ی اندیکاتورهای rolling)."""
    exchange = get_exchange()
    batch = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=500)
    df = pd.DataFrame(batch, columns=["ts", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df = df.set_index("timestamp").drop(columns=["ts"])
    df["source"] = "coinex"
    return df.sort_index()
