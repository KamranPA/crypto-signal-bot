# مسیر فایل: features/indicators.py
"""
معادل پایتونی بخش‌های محاسباتی اندیکاتور Pine Script اصلی (Mutanabby_AI | Fresh Algo V24).

نکات مهم برای جلوگیری از نشت داده (Data Leakage):
- تمام محاسبات فقط از دیتای t و قبل از آن استفاده می‌کنند.
- هیچ shift(-1) یا نگاه به آینده در این فایل مجاز نیست.
- این ماژول توسط هم backtest/engine.py و هم jobs/hourly_signal.py استفاده می‌شود
  تا رفتار بک‌تست و لایو کاملاً یکسان باشد.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr


def atr(df: pd.DataFrame, length: int) -> pd.Series:
    tr = true_range(df)
    return tr.ewm(alpha=1 / length, adjust=False).mean()


def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def hma(series: pd.Series, length: int) -> pd.Series:
    half = int(length / 2)
    sqrt_len = int(np.sqrt(length))
    wma_half = series.rolling(half).apply(_wma, args=(half,), raw=True)
    wma_full = series.rolling(length).apply(_wma, args=(length,), raw=True)
    diff = 2 * wma_half - wma_full
    return diff.rolling(sqrt_len).apply(_wma, args=(sqrt_len,), raw=True)


def _wma(values: np.ndarray, length: int) -> float:
    weights = np.arange(1, length + 1)
    return np.dot(values, weights) / weights.sum()


def rsi(series: pd.Series, length: int) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / length, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def dmi_adx(df: pd.DataFrame, length: int = 14):
    up_move = df["high"].diff()
    down_move = -df["low"].diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    tr = true_range(df)
    atr_ = tr.ewm(alpha=1 / length, adjust=False).mean()
    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(alpha=1 / length, adjust=False).mean() / atr_
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=1 / length, adjust=False).mean() / atr_
    dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)) * 100
    adx = dx.ewm(alpha=1 / length, adjust=False).mean()
    return plus_di, minus_di, adx


def supertrend(df: pd.DataFrame, src_col: str, factor: float, length: int):
    atr_ = atr(df, length)
    src = df[src_col]
    upper_band = src + factor * atr_
    lower_band = src - factor * atr_

    final_upper = upper_band.copy()
    final_lower = lower_band.copy()
    direction = pd.Series(index=df.index, dtype=float)
    st = pd.Series(index=df.index, dtype=float)

    for i in range(1, len(df)):
        if upper_band.iat[i] < final_upper.iat[i - 1] or df["close"].iat[i - 1] > final_upper.iat[i - 1]:
            final_upper.iat[i] = upper_band.iat[i]
        else:
            final_upper.iat[i] = final_upper.iat[i - 1]

        if lower_band.iat[i] > final_lower.iat[i - 1] or df["close"].iat[i - 1] < final_lower.iat[i - 1]:
            final_lower.iat[i] = lower_band.iat[i]
        else:
            final_lower.iat[i] = final_lower.iat[i - 1]

        prev_st = st.iat[i - 1] if i > 1 else final_upper.iat[i - 1]
        if prev_st == final_upper.iat[i - 1]:
            direction.iat[i] = 1 if df["close"].iat[i] > final_upper.iat[i] else -1
        else:
            direction.iat[i] = -1 if df["close"].iat[i] < final_lower.iat[i] else 1

        st.iat[i] = final_lower.iat[i] if direction.iat[i] == 1 else final_upper.iat[i]

    return st, direction


def donchian_trend(df: pd.DataFrame, length: int) -> pd.Series:
    hh = df["high"].rolling(length).max()
    ll = df["low"].rolling(length).min()
    trend = pd.Series(index=df.index, dtype=float)
    trend.iat[0] = 0
    for i in range(1, len(df)):
        if df["close"].iat[i] > hh.shift(1).iat[i]:
            trend.iat[i] = 1
        elif df["close"].iat[i] < ll.shift(1).iat[i]:
            trend.iat[i] = -1
        else:
            trend.iat[i] = trend.iat[i - 1]
    return trend


def wavetrend(src: pd.Series, chl_len: int, avg_len: int):
    esa = ema(src, chl_len)
    d = ema((src - esa).abs(), chl_len)
    ci = (src - esa) / (0.015 * d.replace(0, np.nan))
    wt1 = ema(ci, avg_len)
    wt2 = wt1.rolling(3).mean()
    return wt1, wt2


def reversal_dots(df: pd.DataFrame, ms_tuner: int):
    """معادل Reversal Dot Buy/Sell در کد اصلی (Show_PR)."""
    wt1, wt2 = wavetrend(df["close"], 5 * ms_tuner, 10 * ms_tuner)
    cross_up = (wt1.shift(1) < wt2.shift(1)) & (wt1 >= wt2)
    cross_down = (wt1.shift(1) > wt2.shift(1)) & (wt1 <= wt2)
    buy_dot = cross_up & (wt2 <= -60)
    sell_dot = cross_down & (wt2 >= 60)
    return buy_dot, sell_dot, wt1, wt2


def volume_filter(df: pd.DataFrame, fast: int = 15, slow: int = 20, norm: int = 25) -> pd.Series:
    ema_fast = ema(df["volume"], fast)
    ema_slow = ema(df["volume"], slow)
    ema_norm = ema(df["volume"], norm)
    return ((ema_fast - ema_slow) / ema_norm.replace(0, np.nan)) > 0


def compute_all_indicators(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    df باید ستون‌های open/high/low/close/volume داشته باشد، ایندکس زمانی صعودی.
    params از config/params_default.yaml (بخش indicator) خوانده می‌شود.
    """
    out = df.copy()
    ind = params["indicator"]

    out["ema_fast"] = ema(out["close"], ind["ema_fast"])
    out["ema_slow"] = ema(out["close"], ind["ema_slow"])
    out["hma"] = hma(out["close"], ind["hma_len"])

    st, st_dir = supertrend(out, "close", ind["sensitivity"], ind["st_tuner"])
    out["supertrend"] = st
    out["supertrend_dir"] = st_dir

    out["donchian_trend"] = donchian_trend(out, ind["donchian_len"])

    macd_line, signal_line, hist = macd(out["close"])
    out["macd"] = macd_line
    out["macd_signal"] = signal_line
    out["macd_hist"] = hist

    _, _, adx = dmi_adx(out, ind["adx_len"])
    out["adx"] = adx

    out["vol_filter"] = volume_filter(out, ind["volume_fast"], ind["volume_slow"], ind["volume_norm"])

    buy_dot, sell_dot, wt1, wt2 = reversal_dots(out, ind["ms_tuner"])
    out["reversal_buy_dot"] = buy_dot
    out["reversal_sell_dot"] = sell_dot
    out["wt1"] = wt1
    out["wt2"] = wt2

    out["rsi"] = rsi(out["close"], 14)
    out["atr14"] = atr(out, 14)

    return out
