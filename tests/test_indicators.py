# مسیر فایل: tests/test_indicators.py
"""تست‌های پایه برای اطمینان از صحت محاسبات و عدم نشت داده."""
import numpy as np
import pandas as pd
import pytest

from features.indicators import ema, atr, supertrend, compute_all_indicators
import yaml
from pathlib import Path


def make_dummy_df(n=300, seed=42):
    rng = np.random.default_rng(seed)
    price = 100 + np.cumsum(rng.normal(0, 1, n))
    high = price + rng.uniform(0, 1, n)
    low = price - rng.uniform(0, 1, n)
    df = pd.DataFrame({
        "open": price, "high": high, "low": low, "close": price,
        "volume": rng.uniform(100, 1000, n),
    }, index=pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC"))
    return df


def test_ema_no_lookahead():
    df = make_dummy_df()
    e = ema(df["close"], 20)
    df2 = df.copy()
    df2.iloc[250:, df2.columns.get_loc("close")] = 99999
    e2 = ema(df2["close"], 20)
    assert np.isclose(e.iloc[100], e2.iloc[100])


def test_atr_positive():
    df = make_dummy_df()
    a = atr(df, 14)
    assert (a.dropna() >= 0).all()


def test_supertrend_runs():
    df = make_dummy_df()
    st, direction = supertrend(df, "close", 2.4, 10)
    assert len(st) == len(df)
    assert set(direction.dropna().unique()).issubset({1.0, -1.0})


def test_compute_all_indicators_runs():
    df = make_dummy_df()
    params = yaml.safe_load(
        (Path(__file__).resolve().parent.parent / "config/params_default.yaml").read_text(encoding="utf-8")
    )
    out = compute_all_indicators(df, params)
    for col in ["ema_fast", "ema_slow", "supertrend", "macd", "adx", "wt1", "wt2"]:
        assert col in out.columns
