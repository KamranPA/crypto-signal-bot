# مسیر فایل: data/coinex_client.py
"""دریافت دیتای OHLCV از CoinEx از طریق ccxt — منبع اصلی برای اجرای زنده."""
from __future__ import annotations
import time
from datetime import datetime, timezone, timedelta
import pandas as pd
import ccxt

# طول هر تایم‌فریم به ثانیه — برای تشخیص کندل ناقص (در حال شکل‌گیری)
TIMEFRAME_SECONDS = {
    "1m": 60, "3m": 180, "5m": 300, "15m": 900, "30m": 1800,
    "1h": 3600, "2h": 7200, "4h": 14400, "1d": 86400,
}


def get_exchange() -> ccxt.coinex:
    return ccxt.coinex({"enableRateLimit": True})


def drop_unclosed_candle(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """
    اکثر صرافی‌ها (از جمله CoinEx از طریق ccxt) آخرین کندل برگشتی را همان کندل
    در-حال-شکل‌گیری برمی‌گردانند، نه آخرین کندل واقعاً بسته‌شده. اگر این کندل ناقص
    را برای تشخیص سیگنال (crossover) استفاده کنیم، چون crossover یک شرط لحظه‌ای
    است (فقط دقیقاً روی کندلی که عبور در آن کامل شده True می‌شود)، ممکن است
    سیگنال واقعی را برای همیشه از دست بدهیم — چون ساعت بعد آن کندل دیگر «آخرین»
    نیست و دوباره چک نمی‌شود.

    این تابع اگر آخرین کندل هنوز به پایان نرسیده باشد، آن را حذف می‌کند تا همیشه
    روی آخرین کندل واقعاً بسته‌شده کار کنیم.
    """
    if df.empty:
        return df
    seconds = TIMEFRAME_SECONDS.get(timeframe)
    if seconds is None:
        return df  # تایم‌فریم ناشناخته — دست‌نخورده برگردان

    last_ts = df.index[-1]
    if last_ts.tzinfo is None:
        last_ts = last_ts.tz_localize("UTC")
    candle_close_time = last_ts + timedelta(seconds=seconds)
    now = datetime.now(timezone.utc)

    if candle_close_time > now:
        return df.iloc[:-1]
    return df


def fetch_ohlcv(symbol: str, timeframe: str = "1h", since_ms: int | None = None,
                 limit: int = 1000) -> pd.DataFrame:
    """
    symbol مثل "BTC/USDT". خروجی: DataFrame با ایندکس زمانی UTC و ستون‌های
    open/high/low/close/volume، مرتب صعودی. کندل ناقص (در حال شکل‌گیری) حذف می‌شود.
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
    df = df.sort_index()
    return drop_unclosed_candle(df, timeframe)


def fetch_latest_candle(symbol: str, timeframe: str = "1h") -> pd.DataFrame:
    """برای job ساعتی: فقط چند کندل آخر (کافی برای محاسبه‌ی اندیکاتورهای rolling)."""
    exchange = get_exchange()
    batch = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=500)
    df = pd.DataFrame(batch, columns=["ts", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df = df.set_index("timestamp").drop(columns=["ts"])
    df["source"] = "coinex"
    df = df.sort_index()
    return drop_unclosed_candle(df, timeframe)
