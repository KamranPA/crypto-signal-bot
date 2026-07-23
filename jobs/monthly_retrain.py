# مسیر فایل: jobs/monthly_retrain.py
"""
اسکریپت اجرای ماهانه — توسط .github/workflows/monthly_retrain.yml اجرا می‌شود.

مراحل:
  ۱. دریافت داده‌ی تازه از هر دو منبع (Yahoo برای تاریخچه، CoinEx برای بخش اخیر/زنده)
  ۲. کالیبراسیون و ساخت دیتاست بک‌تست ترکیبی
  ۳. بهینه‌سازی Optuna پارامترهای ریسک (مستقل از مدل ML)
  ۴. Labeling (Triple-Barrier) + ری‌ترین مدل ML هر ارز
  ۵. انتخاب آستانه‌ی ML واقعی از روی منحنی precision-recall مدل تازه train‌شده
  ۶. بک‌تست مقایسه‌ای (خام در برابر فیلترشده‌ی ML) روی test split برای تصمیم این‌که
     آیا فیلتر ML اصلاً برای این ارز کمک می‌کند یا نه (use_ml_filter)
  ۷. بررسی پایداری پارامتر + مقایسه با نسخه‌ی فعلی → پذیرش/رد
  ۸. ذخیره در Supabase + تولید گزارش بک‌تست به‌روز (commit در گیت‌هاب)
"""
from __future__ import annotations
import logging
import yaml
from pathlib import Path
from datetime import datetime, timezone

from data.coinex_client import fetch_ohlcv as coinex_fetch
from data.yahoo_client import fetch_ohlcv as yahoo_fetch
from data.calibration import build_calibrated_history
from strategy.core import generate_raw_signals
from ml.labeling import build_labeled_dataset
from ml.train import train_model
from ml.threshold import select_ml_threshold
from ml.predict import load_latest_model
from ml.optimize import optimize_risk_and_threshold
from backtest.engine import run_backtest
from backtest.ml_filtered import run_ml_filtered_backtest, decide_use_ml_filter, print_comparison
from backtest.report_generator import generate_html_report, generate_summary_md
from storage.supabase_client import get_client, save_param_version, get_active_params

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("monthly_retrain")

ROOT = Path(__file__).resolve().parent.parent


def load_config():
    watchlist = yaml.safe_load((ROOT / "config/watchlist.yaml").read_text(encoding="utf-8"))
    params_default = yaml.safe_load((ROOT / "config/params_default.yaml").read_text(encoding="utf-8"))
    return watchlist, params_default


def months_since_project_start(start_date: str = "2026-07-01") -> int:
    start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    return max(1, (now.year - start.year) * 12 + (now.month - start.month) + 1)


def run():
    watchlist, params_default = load_config()
    client = get_client()
    reports = []

    for coin in watchlist["coins"]:
        symbol_name = coin["name"]
        log.info(f"=== Retraining {symbol_name} ===")

        try:
            df_yahoo = yahoo_fetch(coin["yahoo_symbol"], period=f"{watchlist['backtest_years']*365}d",
                                    interval="1h")
            df_coinex = coinex_fetch(coin["coinex_symbol"], watchlist["timeframe"])
            df_combined = build_calibrated_history(df_yahoo, df_coinex)

            d = generate_raw_signals(df_combined, params_default)

            # --- بهینه‌سازی پارامترهای ریسک (مستقل از مدل ML) ---
            search_space = params_default["risk_defaults"]["search_space"]
            months = months_since_project_start()
            result = optimize_risk_and_threshold(
                df_backtest=df_combined,
                df_live=df_coinex,
                symbol=symbol_name,
                indicator_params=params_default,
                search_space=search_space,
                months_since_start=months,
                blending_schedule=params_default["blending_schedule_months"],
                n_trials=60,
            )

            best_risk = {
                "atr_mult": result["best_params"]["atr_mult"],
                "tp1_r": result["best_params"]["tp1_r"],
                "tp2_r": result["best_params"]["tp2_r"],
                "tp3_r": result["best_params"]["tp3_r"],
            }

            # --- مقایسه با نسخه‌ی فعلی ریسک؛ پذیرش فقط با بهبود معنادار ---
            active = get_active_params(client, symbol_name)
            accepted = True
            notes = "اولین نسخه" if not active else ""
            if active:
                current_report = run_backtest(df_combined, symbol_name, params_default, {
                    "atr_mult": active["atr_mult"], "tp1_r": active["tp1_r"],
                    "tp2_r": active["tp2_r"], "tp3_r": active["tp3_r"],
                })
                new_report = run_backtest(df_combined, symbol_name, params_default, best_risk)
                improvement = (new_report.profit_factor - current_report.profit_factor)
                accepted = improvement > 0.1
                notes = f"بهبود Profit Factor: {improvement:+.2f}"

            final_risk = best_risk if accepted else {
                "atr_mult": active["atr_mult"], "tp1_r": active["tp1_r"],
                "tp2_r": active["tp2_r"], "tp3_r": active["tp3_r"],
            } if active else params_default["risk_defaults"]

            # --- ری‌ترین ML با پارامترهای ریسک نهایی ---
            labeled = build_labeled_dataset(d, symbol_name, final_risk)
            ml_threshold = params_default["ml_defaults"]["confidence_threshold"]
            use_ml_filter = True  # پیش‌فرض محافظه‌کارانه تا مقایسه‌ی واقعی انجام شود

            if len(labeled) >= 30:
                train_result = train_model(labeled, symbol_name)
                pr_curve = train_result["metrics"]["precision_recall_curve"]
                ml_threshold = select_ml_threshold(
                    pr_curve["precision"], pr_curve["recall"], pr_curve["thresholds"],
                    min_recall=0.05,
                    default=params_default["ml_defaults"]["confidence_threshold"],
                )
                log.info(f"{symbol_name}: آستانه‌ی ML از منحنی precision-recall واقعی انتخاب شد: "
                         f"{ml_threshold:.3f} (قبلاً ثابت: {params_default['ml_defaults']['confidence_threshold']})")

                # --- تصمیم: آیا فیلتر ML برای این ارز واقعاً کمک می‌کند؟ (روی test split) ---
                fresh_model = load_latest_model(symbol_name)
                full_report_ml, filtered_report_ml = run_ml_filtered_backtest(
                    df_combined, symbol_name, params_default, final_risk,
                    fresh_model, ml_threshold, test_only=True,
                )
                print_comparison(symbol_name, full_report_ml, filtered_report_ml)
                use_ml_filter = decide_use_ml_filter(full_report_ml, filtered_report_ml)
                log.info(f"{symbol_name}: use_ml_filter = {use_ml_filter}")
            else:
                log.warning(f"{symbol_name}: داده‌ی کافی برای ری‌ترین ML نیست ({len(labeled)} نمونه) — "
                            f"آستانه‌ی پیش‌فرض ({ml_threshold}) و use_ml_filter=True نگه داشته می‌شود")

            # --- ذخیره‌ی پارامتر نهایی (ریسک + آستانه‌ی واقعی ML + تصمیم فیلتر) ---
            save_param_version(
                client, symbol_name, result.get("version", "n/a"), final_risk,
                ml_threshold=ml_threshold,
                adjusted_score=result["best_score"],
                weights=result["blending_weights"],
                accepted=accepted, notes=notes,
                use_ml_filter=use_ml_filter,
            )

            # --- گزارش بک‌تست به‌روز (rule-based کامل، برای مرجع کلی) ---
            report = run_backtest(df_combined, symbol_name, params_default, final_risk)
            generate_html_report(report)
            reports.append(report)

            log.info(f"{symbol_name}: accepted={accepted}, n_trades={report.n_trades}, "
                     f"win_rate={report.win_rate:.1%}, ml_threshold={ml_threshold:.3f}, "
                     f"use_ml_filter={use_ml_filter}")

        except Exception as e:
            log.exception(f"Error retraining {symbol_name}: {e}")
            continue

    generate_summary_md(reports)


if __name__ == "__main__":
    run()
