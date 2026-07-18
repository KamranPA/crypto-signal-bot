# مسیر فایل: ml/optimize.py
"""
بهینه‌سازی خودکار پارامترهای ریسک (TP/SL) و آستانه‌ی ML — مطابق architecture.md بخش ۶ و ۷.

فاز ۱: فقط گروه ریسک و ML باز هستند (پارامترهای هسته‌ی اندیکاتور ثابت می‌مانند).
تابع هدف: adjusted_score = monthly_score * confidence_factor(n_trades)
  که خودش بدون قید سخت، بین کیفیت (win rate/expectancy) و کمیت (تعداد معامله) تعادل برقرار می‌کند.
"""
from __future__ import annotations
import math
from datetime import datetime, timezone
import optuna
import pandas as pd

from backtest.engine import run_backtest, BacktestReport

optuna.logging.set_verbosity(optuna.logging.WARNING)


def confidence_factor(n_trades: int, min_reliable: int = 8) -> float:
    """
    جریمه‌ی نمونه‌ی کم — مشابه فلسفه‌ی Wilson score interval.
    وقتی تعداد معامله خیلی کم است (آماره غیرقابل‌اعتماد)، امتیاز به‌شدت تضعیف می‌شود.
    با نزدیک شدن به min_reliable و بیشتر، ضریب به ۱ میل می‌کند.
    """
    if n_trades <= 0:
        return 0.0
    return 1 - math.exp(-n_trades / min_reliable)


def compute_adjusted_score(report: BacktestReport, months_covered: float) -> float:
    closed = report.closed_trades  # open_at_end از محاسبه حذف می‌شود (نتیجه‌ی واقعی نامعلوم است)
    n_closed = len(closed)
    if n_closed == 0 or months_covered <= 0:
        return -math.inf

    wins = [t for t in closed if t.outcome != "sl"]
    losses = [t for t in closed if t.outcome == "sl"]
    win_rate = len(wins) / n_closed
    loss_rate = len(losses) / n_closed
    avg_win = sum(t.pnl_pct for t in wins) / len(wins) if wins else 0.0
    avg_loss = -sum(t.pnl_pct for t in losses) / len(losses) if losses else 0.0

    expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)
    trades_per_month = n_closed / months_covered
    monthly_score = trades_per_month * expectancy

    return monthly_score * confidence_factor(n_closed)


def get_blending_weights(months_since_start: int, schedule: list[dict]) -> tuple[float, float]:
    """خطی بین نقاط جدول blending_schedule_months از params_default.yaml درون‌یابی می‌کند."""
    schedule = sorted(schedule, key=lambda x: x["month"])
    if months_since_start <= schedule[0]["month"]:
        return schedule[0]["backtest_weight"], schedule[0]["live_weight"]
    if months_since_start >= schedule[-1]["month"]:
        return schedule[-1]["backtest_weight"], schedule[-1]["live_weight"]

    for a, b in zip(schedule, schedule[1:]):
        if a["month"] <= months_since_start <= b["month"]:
            span = b["month"] - a["month"]
            t = (months_since_start - a["month"]) / span if span else 0
            bw = a["backtest_weight"] + t * (b["backtest_weight"] - a["backtest_weight"])
            lw = a["live_weight"] + t * (b["live_weight"] - a["live_weight"])
            return bw, lw
    return schedule[-1]["backtest_weight"], schedule[-1]["live_weight"]


def walk_forward_windows(df: pd.DataFrame, n_windows: int = 4):
    """df را به n_windows بازه‌ی متوالی تقسیم می‌کند: هر بازه هم train هم validation (بازه‌ی بعدی) دارد."""
    size = len(df) // (n_windows + 1)
    for i in range(n_windows):
        train = df.iloc[: size * (i + 1)]
        valid = df.iloc[size * (i + 1): size * (i + 2)]
        if len(valid) < 20:
            continue
        yield train, valid


def optimize_risk_and_threshold(df_backtest: pd.DataFrame, df_live: pd.DataFrame | None,
                                 symbol: str, indicator_params: dict, search_space: dict,
                                 months_since_start: int, blending_schedule: list[dict],
                                 n_trials: int = 60) -> dict:
    """
    خروجی: بهترین پارامترهای ریسک + آستانه‌ی ML برای این ارز، همراه با متادیتای پایداری
    (برای بررسی نوسان پارامتر بین دوره‌ها در جاب ماهانه).
    """
    bw, lw = get_blending_weights(months_since_start, blending_schedule)

    def objective(trial: optuna.Trial) -> float:
        risk_params = {
            "atr_mult": trial.suggest_float("atr_mult", *search_space["atr_mult"]),
            "tp1_r": trial.suggest_float("tp1_r", *search_space["tp1_r"]),
            "tp2_r": trial.suggest_float("tp2_r", *search_space["tp2_r"]),
            "tp3_r": trial.suggest_float("tp3_r", *search_space["tp3_r"]),
        }
        if not (risk_params["tp1_r"] < risk_params["tp2_r"] < risk_params["tp3_r"]):
            raise optuna.TrialPruned()  # ترتیب منطقی TP ها باید حفظ شود

        scores = []
        for train_win, valid_win in walk_forward_windows(df_backtest):
            report = run_backtest(valid_win, symbol, indicator_params, risk_params)
            months = (valid_win.index[-1] - valid_win.index[0]).days / 30.0
            scores.append(compute_adjusted_score(report, max(months, 0.1)))

        backtest_score = sum(scores) / len(scores) if scores else -math.inf

        live_score = backtest_score  # مقدار پیش‌فرض تا داده‌ی زنده‌ی کافی جمع شود
        if df_live is not None and len(df_live) > 50:
            live_report = run_backtest(df_live, symbol, indicator_params, risk_params)
            live_months = (df_live.index[-1] - df_live.index[0]).days / 30.0
            live_score = compute_adjusted_score(live_report, max(live_months, 0.1))

        return bw * backtest_score + lw * live_score

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    return {
        "symbol": symbol,
        "version": datetime.now(timezone.utc).strftime("%Y%m%d%H%M"),  # اصلاح‌شده: قبلاً این کلید اصلاً وجود نداشت
        "best_params": study.best_params,
        "best_score": study.best_value,
        "blending_weights": {"backtest": bw, "live": lw},
        "n_trials": n_trials,
    }


def check_parameter_stability(history: list[dict], param_name: str, tolerance: float = 0.35) -> bool:
    """
    اگر مقدار پارامتر در ۳ دوره‌ی اخیر بیش از tolerance (نسبی) نوسان کند، ناپایدار تلقی می‌شود
    و باید از میانگین متحرک به‌جای مقدار خام جدید استفاده شود (architecture.md بخش ۷).
    """
    recent = [h["best_params"][param_name] for h in history[-3:] if param_name in h.get("best_params", {})]
    if len(recent) < 2:
        return True
    spread = (max(recent) - min(recent)) / (abs(sum(recent) / len(recent)) + 1e-9)
    return spread <= tolerance
