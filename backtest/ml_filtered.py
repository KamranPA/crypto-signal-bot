# مسیر فایل: backtest/ml_filtered.py
"""
بک‌تست «کل سیستم» — یعنی سیگنال rule-based + فیلتر واقعی مدل ML، نه فقط منطق خام.

نکته‌ی حیاتی برای جلوگیری از نتیجه‌ی گمراه‌کننده (look-ahead bias):
مدل ML روی ۷۰٪ اول داده train شده (ml/train.py: walk_forward_split, train_ratio=0.7).
این ماژول فقط روی همان ۳۰٪ انتهایی (test split — داده‌ای که مدل موقع آموزش ندیده) کار
می‌کند تا نتیجه منصفانه باشد.

اضافه‌شده: decide_use_ml_filter — تصمیم خودکار این‌که آیا فیلتر ML برای این ارز به‌طور
مشخص کمک می‌کند یا نه. بعضی ارزها (طبق داده‌ی واقعی) با فیلتر ML بدتر می‌شوند، نه بهتر —
برای آن‌ها بهتر است سیگنال خام (بدون فیلتر) ارسال شود.
"""
from __future__ import annotations
import math
import pandas as pd

from strategy.core import generate_raw_signals, build_signal
from backtest.engine import (
    BacktestReport, _simulate_exit, compute_position_fraction,
)
from ml.predict import predict_confidence

TRAIN_RATIO = 0.7  # باید دقیقاً با ml/train.py:walk_forward_split هم‌خوان باشد


def split_test_portion(df: pd.DataFrame, train_ratio: float = TRAIN_RATIO) -> pd.DataFrame:
    """فقط بخش انتهایی (داده‌ای که مدل موقع آموزش ندیده) را برمی‌گرداند."""
    split_idx = int(len(df) * train_ratio)
    return df.iloc[split_idx:]


def run_ml_filtered_backtest(df: pd.DataFrame, symbol: str, params: dict, risk_params: dict,
                              model, ml_threshold: float, test_only: bool = True) -> tuple[BacktestReport, BacktestReport]:
    """
    خروجی: (گزارش کامل rule-based، گزارش فیلترشده‌ی ML) — هر دو روی همان بازه‌ی داده.
    اگر test_only=True (پیش‌فرض)، فقط روی بخش انتهایی (test split) اجرا می‌شود.
    """
    d_full = generate_raw_signals(df, params)
    d = split_test_portion(d_full, TRAIN_RATIO) if test_only else d_full

    execution = params.get("execution", {"fee_pct_per_side": 0.0, "slippage_pct_per_side": 0.0})
    cost_pct = 2 * (execution.get("fee_pct_per_side", 0.0) + execution.get("slippage_pct_per_side", 0.0))
    sizing = params.get("position_sizing", {"risk_per_trade_pct": 1.0, "max_position_pct": 100.0})
    risk_per_trade_pct = sizing.get("risk_per_trade_pct", 1.0)
    max_position_pct = sizing.get("max_position_pct", 100.0)

    full_report = BacktestReport(symbol=symbol)
    filtered_report = BacktestReport(symbol=symbol)

    i = 0
    while i < len(d):
        row = d.iloc[i]
        if row.get("bull") or row.get("bear"):
            sig = build_signal(d, i, symbol, risk_params)
            if sig is not None:
                position_fraction = compute_position_fraction(
                    sig.entry, sig.stop_loss, risk_per_trade_pct, max_position_pct
                )
                trade = _simulate_exit(d, i, sig, cost_pct=cost_pct, position_fraction=position_fraction)
                full_report.trades.append(trade)

                if model is not None:
                    confidence = predict_confidence(model, d, i)
                    if confidence >= ml_threshold:
                        filtered_report.trades.append(trade)

                i += max(trade.bars_held, 1)
                continue
        i += 1

    return full_report, filtered_report


def decide_use_ml_filter(full_report: BacktestReport, filtered_report: BacktestReport,
                          margin: float = 0.05, min_trades: int = 15) -> bool:
    """
    تصمیم می‌گیرد آیا فیلتر ML برای این ارز واقعاً کمک می‌کند یا نه، بر اساس مقایسه‌ی
    Profit Factor خام در برابر فیلترشده روی همان test split.
    """
    n_raw = len(full_report.closed_trades)
    if n_raw < min_trades:
        return True

    raw_pf = full_report.profit_factor
    filt_pf = filtered_report.profit_factor

    if math.isnan(raw_pf) or math.isnan(filt_pf):
        return True

    if math.isinf(raw_pf) and math.isinf(filt_pf):
        return True
    if math.isinf(filt_pf) and not math.isinf(raw_pf):
        return True
    if math.isinf(raw_pf) and not math.isinf(filt_pf):
        return False

    return filt_pf > (raw_pf + margin)


def print_comparison(symbol: str, full_report: BacktestReport, filtered_report: BacktestReport):
    """چاپ خلاصه‌ی مقایسه‌ی rule-based خام در برابر فیلترشده‌ی ML، برای لاگ/کنسول."""
    def fmt(report: BacktestReport) -> str:
        n = len(report.closed_trades)
        if n == 0:
            return "n=   0  (هیچ معامله‌ای در این بازه نبود — نمی‌توان قضاوت کرد)"
        return (f"n={n:4d}  win_rate={report.win_rate:.1%}  "
                f"PF={report.profit_factor:.2f}  avg_pnl={report.avg_pnl_pct:.2f}%  "
                f"DD={report.max_drawdown_pct:.2f}%")

    print(f"=== {symbol}: rule-based خام در برابر فیلترشده‌ی ML (فقط روی test split) ===")
    print(f"  خام      : {fmt(full_report)}")
    print(f"  فیلترشده : {fmt(filtered_report)}")
