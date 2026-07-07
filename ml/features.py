# مسیر فایل: ml/features.py
"""استخراج فیچرهای ورودی مدل ML — فقط از اطلاعات موجود تا لحظه‌ی سیگنال (idx)."""
from __future__ import annotations
import pandas as pd

FEATURE_COLUMNS = [
    "rsi", "adx", "macd_hist", "wt2",
    "close_vs_ema_fast", "close_vs_ema_slow", "close_vs_hma",
    "atr_pct", "vol_filter", "donchian_trend", "direction_bull",
]


def extract_feature_row(df: pd.DataFrame, idx: int) -> dict:
    row = df.iloc[idx]
    close = row["close"]
    return {
        "rsi": row["rsi"],
        "adx": row["adx"],
        "macd_hist": row["macd_hist"],
        "wt2": row["wt2"],
        "close_vs_ema_fast": (close - row["ema_fast"]) / close,
        "close_vs_ema_slow": (close - row["ema_slow"]) / close,
        "close_vs_hma": (close - row["hma"]) / close,
        "atr_pct": row["atr14"] / close,
        "vol_filter": int(bool(row["vol_filter"])),
        "donchian_trend": row["donchian_trend"],
        "direction_bull": int(bool(row.get("bull"))),
    }
