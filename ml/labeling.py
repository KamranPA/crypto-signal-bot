# مسیر فایل: ml/labeling.py
"""
Triple-Barrier Labeling. برای هر سیگنال rule-based، برچسب بر اساس این‌که TP یا SL
زودتر لمس شود ساخته می‌شود. این تنها جای مجاز برای "نگاه به آینده" است — فقط برای
ساخت لیبل، نه برای فیچرهای ورودی مدل.
"""
from __future__ import annotations
import pandas as pd
from backtest.engine import _simulate_exit
from strategy.core import Signal


def label_signal(df: pd.DataFrame, entry_idx: int, sig: Signal) -> int:
    """1 = سیگنال موفق (به TP1+ رسید قبل از SL) | 0 = ناموفق (SL خورد)"""
    trade = _simulate_exit(df, entry_idx, sig)
    return 1 if trade.outcome in ("tp1", "tp2", "tp3") else 0


def build_labeled_dataset(df_with_signals: pd.DataFrame, symbol: str, risk_params: dict) -> pd.DataFrame:
    from strategy.core import build_signal
    from ml.features import extract_feature_row

    rows = []
    for i in range(len(df_with_signals)):
        row = df_with_signals.iloc[i]
        if not (row.get("bull") or row.get("bear")):
            continue
        sig = build_signal(df_with_signals, i, symbol, risk_params)
        if sig is None:
            continue
        label = label_signal(df_with_signals, i, sig)
        features = extract_feature_row(df_with_signals, i)
        features["label"] = label
        features["timestamp"] = df_with_signals.index[i]
        rows.append(features)

    return pd.DataFrame(rows)
