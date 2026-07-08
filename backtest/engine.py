# مسیر فایل: backtest/engine.py
"""
موتور بک‌تست — از همان strategy/core.py استفاده می‌کند که در Live هم مصرف می‌شود
تا هیچ اختلاف منطقی بین بک‌تست و اجرای زنده وجود نداشته باشد.

شبیه‌سازی خروج: برای هر سیگنال، کندل‌های بعدی پیمایش می‌شوند تا اولین برخورد با
SL یا یکی از TPها (به ترتیب زمانی) پیدا شود. اگر SL و TP در یک کندل هر دو لمس شوند،
به‌صورت محافظه‌کارانه SL زودتر فرض می‌شود (سناریوی بدبینانه).
"""
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
    def closed_trades(self) -> list[TradeResult]:
        """معاملاتی که واقعاً به TP یا SL رسیده‌اند (نه تا انتهای دیتا بدون نتیجه مانده‌اند)."""
        return [t for t in self.trades if t.outcome != "open_at_end"]

    @property
    def n_open_at_end(self) -> int:
        """
        تعداد معاملاتی که در بازه‌ی max_bars نه TP نه SL خورده‌اند.
        قبلاً این معاملات به‌اشتباه در win_rate جزو «برد» حساب می‌شدند — رفع شد.
        اگر این عدد بالا باشد (مثلاً بیش از ۱۰-۱۵٪ کل معاملات)، یعنی TP/SL برای
        تایم‌فریم انتخابی خیلی دور از قیمت تنظیم شده و باید ریسک/ATR بازبینی شود.
        """
        return self.n_trades - len(self.closed_trades)

    @property
    def win_rate(self) -> float:
        closed = self.closed_trades
        if not closed:
            return 0.0
        wins = [t for t in closed if t.outcome != "sl"]
        return len(wins) / len(closed)

    @property
    def avg_pnl_pct(self) -> float:
        closed = self.closed_trades
        if not closed:
            return 0.0
        return sum(t.pnl_pct for t in closed) / len(closed)

    @property
    def profit_factor(self) -> float:
        closed = self.closed_trades
        gains = sum(t.pnl_pct for t in closed if t.pnl_pct > 0)
        losses = -sum(t.pnl_pct for t in closed if t.pnl_pct < 0)
        return gains / losses if losses > 0 else float("inf")

    @property
    def max_drawdown_pct(self) -> float:
        closed = self.closed_trades
        if not closed:
            return 0.0
        equity = (1 + pd.Series([t.pnl_pct for t in closed]) / 100).cumprod()
        running_max = equity.cummax()
        drawdown = (equity - running_max) / running_max
        return float(drawdown.min() * 100)


def _simulate_exit(df: pd.DataFrame, entry_idx: int, sig: Signal, cost_pct: float = 0.0,
                    max_bars: int = 500) -> TradeResult:
    """
    cost_pct: هزینه‌ی رفت‌وبرگشت معامله (کارمزد ورود + خروج + اسلیپیج تخمینی)، به‌درصد.
    از هر خروجی (TP یا SL) کم می‌شود تا نتیجه واقع‌بینانه باشد.
    """
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
            pnl = _pct(sig.entry, sig.stop_loss, sig.direction, cost_pct)
            return TradeResult(sig, "sl", sig.stop_loss, ts, pnl, len(future.loc[:ts]))
        if hit_tp3:
            pnl = _pct(sig.entry, sig.tp3, sig.direction, cost_pct)
            return TradeResult(sig, "tp3", sig.tp3, ts, pnl, len(future.loc[:ts]))
        if hit_tp2:
            pnl = _pct(sig.entry, sig.tp2, sig.direction, cost_pct)
            return TradeResult(sig, "tp2", sig.tp2, ts, pnl, len(future.loc[:ts]))
        if hit_tp1:
            pnl = _pct(sig.entry, sig.tp1, sig.direction, cost_pct)
            return TradeResult(sig, "tp1", sig.tp1, ts, pnl, len(future.loc[:ts]))

    # نه SL نه TP لمس نشد تا انتهای دیتا — این معامله در محاسبه‌ی متریک‌ها لحاظ نمی‌شود
    # (BacktestReport.closed_trades) چون نتیجه‌ی واقعی‌اش معلوم نیست.
    last_row = future.iloc[-1] if len(future) else df.iloc[entry_idx]
    pnl = _pct(sig.entry, last_row["close"], sig.direction, cost_pct)
    return TradeResult(sig, "open_at_end", last_row["close"], future.index[-1] if len(future) else sig.timestamp,
                        pnl, len(future))


def _pct(entry: float, exit_price: float, direction: str, cost_pct: float = 0.0) -> float:
    if direction == "bull":
        raw = (exit_price - entry) / entry * 100
    else:
        raw = (entry - exit_price) / entry * 100
    return raw - cost_pct


def run_backtest(df: pd.DataFrame, symbol: str, params: dict, risk_params: dict) -> BacktestReport:
    """
    df: دیتای OHLCV (خروجی data/calibration.py برای بک‌تست ترکیبی، یا خام برای فقط-CoinEx)
    params: از config/params_default.yaml (شامل بخش‌های indicator و execution)
    risk_params: baseline یا خروجی Optuna برای این ارز
    """
    d = generate_raw_signals(df, params)
    report = BacktestReport(symbol=symbol)

    execution = params.get("execution", {"fee_pct_per_side": 0.0, "slippage_pct_per_side": 0.0})
    # هزینه‌ی رفت‌وبرگشت = ۲× (کارمزد + اسلیپیج) چون هم در ورود هم در خروج اعمال می‌شود
    cost_pct = 2 * (execution.get("fee_pct_per_side", 0.0) + execution.get("slippage_pct_per_side", 0.0))

    i = 0
    while i < len(d):
        row = d.iloc[i]
        if row.get("bull") or row.get("bear"):
            sig = build_signal(d, i, symbol, risk_params)
            if sig is not None:
                trade = _simulate_exit(d, i, sig, cost_pct=cost_pct)
                report.trades.append(trade)
                # جلوگیری از هم‌پوشانی معاملات: بعد از یک سیگنال، تا خروج آن سیگنال دیگری باز نمی‌شود
                i += max(trade.bars_held, 1)
                continue
        i += 1

    return report
