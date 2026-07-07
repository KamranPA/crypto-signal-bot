# مسیر فایل: backtest/engine.py
"""موتور بک‌تست — از strategy/core.py استفاده می‌کند که در Live هم مصرف می‌شود."""
from __future__ import annotations
from dataclasses import dataclass, field
import pandas as pd

from strategy.core import generate_raw_signals, build_signal, Signal


@dataclass
class TradeResult:
    signal: Signal
    outcome: str          # "tp1" / "tp2" / "tp3" / "sl" / "open_at_end"
    exit_price: float
    exit_time: pd.Timestamp
    pnl_pct: float
    bars_held: int


@dataclass
class BacktestReport:
    symbol: str
    trades: list[TradeResult] = field(default_factory=list)

    @property
    def n_trades(self) -> int:
        return len(self.trades)

    @property
    def win_rate(self) -> float:
        wins = [t for t in self.trades if t.outcome != "sl"]
        return len(wins) / self.n_trades if self.n_trades else 0.0

    @property
    def avg_pnl_pct(self) -> float:
        if not self.trades:
            return 0.0
        return sum(t.pnl_pct for t in self.trades) / len(self.trades)

    @property
    def profit_factor(self) -> float:
        gains = sum(t.pnl_pct for t in self.trades if t.pnl_pct > 0)
        losses = -sum(t.pnl_pct for t in self.trades if t.pnl_pct < 0)
        return gains / losses if losses > 0 else float("inf")

    @property
    def max_drawdown_pct(self) -> float:
        if not self.trades:
            return 0.0
        equity = (1 + pd.Series([t.pnl_pct for t in self.trades]) / 100).cumprod()
        running_max = equity.cummax()
        drawdown = (equity - running_max) / running_max
        return float(drawdown.min() * 100)


def _simulate_exit(df: pd.DataFrame, entry_idx: int, sig: Signal, max_bars: int = 500) -> TradeResult:
    future = df.iloc[entry_idx + 1: entry_idx + 1 + max_bars]

    for ts, row in future.iterrows():
        if sig.direction == "bull":
            hit_sl = row["low"] <= sig.stop_loss
            hit_tp3 = row["high"] >= sig.tp3
            hit_tp2 = row["high"] >= sig.tp2
            hit_tp1 = row["high"] >= sig.tp1
        else:
            hit_sl = row["high"] >= sig.stop_loss
            hit_tp3 = row["low"] <= sig.tp3
            hit_tp2 = row["low"] <= sig.tp2
            hit_tp1 = row["low"] <= sig.tp1

        if hit_sl:  # فرض محافظه‌کارانه: SL در همان کندل زودتر از TP فرض می‌شود
            pnl = _pct(sig.entry, sig.stop_loss, sig.direction)
            return TradeResult(sig, "sl", sig.stop_loss, ts, pnl, len(future.loc[:ts]))
        if hit_tp3:
            pnl = _pct(sig.entry, sig.tp3, sig.direction)
            return TradeResult(sig, "tp3", sig.tp3, ts, pnl, len(future.loc[:ts]))
        if hit_tp2:
            pnl = _pct(sig.entry, sig.tp2, sig.direction)
            return TradeResult(sig, "tp2", sig.tp2, ts, pnl, len(future.loc[:ts]))
        if hit_tp1:
            pnl = _pct(sig.entry, sig.tp1, sig.direction)
            return TradeResult(sig, "tp1", sig.tp1, ts, pnl, len(future.loc[:ts]))

    last_row = future.iloc[-1] if len(future) else df.iloc[entry_idx]
    pnl = _pct(sig.entry, last_row["close"], sig.direction)
    return TradeResult(sig, "open_at_end", last_row["close"], future.index[-1] if len(future) else sig.timestamp,
                        pnl, len(future))


def _pct(entry: float, exit_price: float, direction: str) -> float:
    if direction == "bull":
        return (exit_price - entry) / entry * 100
    return (entry - exit_price) / entry * 100


def run_backtest(df: pd.DataFrame, symbol: str, indicator_params: dict, risk_params: dict) -> BacktestReport:
    d = generate_raw_signals(df, indicator_params)
    report = BacktestReport(symbol=symbol)

    i = 0
    while i < len(d):
        row = d.iloc[i]
        if row.get("bull") or row.get("bear"):
            sig = build_signal(d, i, symbol, risk_params)
            if sig is not None:
                trade = _simulate_exit(d, i, sig)
                report.trades.append(trade)
                i += max(trade.bars_held, 1)
                continue
        i += 1

    return report
