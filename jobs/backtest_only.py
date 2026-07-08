# مسیر فایل: jobs/backtest_only.py
"""
اسکریپت بک‌تست مستقل و سریع — جدا از jobs/monthly_retrain.py.

برخلاف job ماهانه (که بهینه‌سازی Optuna + ری‌ترین ML را هم انجام می‌دهد و سنگین است)،
این اسکریپت فقط بک‌تست را با پارامترهای فعلی (baseline یا آخرین نسخه‌ی پذیرفته‌شده
در Supabase، اگر موجود باشد) اجرا می‌کند و گزارش HTML تولید می‌کند.

استفاده:
    python -m jobs.backtest_only                  # همه‌ی واچ‌لیست
    python -m jobs.backtest_only --symbol BTC      # فقط یک ارز
    python -m jobs.backtest_only --coinex-only     # بدون Yahoo (سریع‌تر، فقط تاریخچه‌ی کوتاه CoinEx)
"""
from __future__ import annotations
import argparse
import logging
import yaml
from pathlib import Path

from data.coinex_client import fetch_ohlcv as coinex_fetch
from data.yahoo_client import fetch_ohlcv as yahoo_fetch
from data.calibration import build_calibrated_history
from backtest.engine import run_backtest
from backtest.report_generator import generate_html_report, generate_summary_md

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("backtest_only")

ROOT = Path(__file__).resolve().parent.parent


def load_config():
    watchlist = yaml.safe_load((ROOT / "config/watchlist.yaml").read_text(encoding="utf-8"))
    params_default = yaml.safe_load((ROOT / "config/params_default.yaml").read_text(encoding="utf-8"))
    return watchlist, params_default


def get_risk_params(symbol: str, params_default: dict) -> dict:
    """تلاش می‌کند آخرین پارامتر پذیرفته‌شده از Supabase را بگیرد؛ در غیر این صورت baseline."""
    try:
        from storage.supabase_client import get_client, get_active_params
        client = get_client()
        active = get_active_params(client, symbol)
        if active:
            return {
                "atr_mult": active["atr_mult"], "tp1_r": active["tp1_r"],
                "tp2_r": active["tp2_r"], "tp3_r": active["tp3_r"],
            }
    except Exception as e:
        log.warning(f"عدم دسترسی به Supabase ({e})، استفاده از پارامترهای baseline.")
    return params_default["risk_defaults"]


def run(symbol_filter: str | None = None, coinex_only: bool = False):
    watchlist, params_default = load_config()
    reports = []

    for coin in watchlist["coins"]:
        symbol_name = coin["name"]
        if symbol_filter and symbol_name != symbol_filter:
            continue

        log.info(f"=== Backtesting {symbol_name} ===")
        try:
            df_coinex = coinex_fetch(coin["coinex_symbol"], watchlist["timeframe"])

            if coinex_only:
                df = df_coinex
            else:
                df_yahoo = yahoo_fetch(coin["yahoo_symbol"],
                                        period=f"{watchlist['backtest_years']*365}d", interval="1h")
                df = build_calibrated_history(df_yahoo, df_coinex)

            risk_params = get_risk_params(symbol_name, params_default)
            report = run_backtest(df, symbol_name, params_default, risk_params)

            path = generate_html_report(report)
            reports.append(report)

            log.info(f"{symbol_name}: n_trades={report.n_trades}, win_rate={report.win_rate:.1%}, "
                      f"profit_factor={report.profit_factor:.2f} → گزارش: {path}")

        except Exception as e:
            log.exception(f"خطا در بک‌تست {symbol_name}: {e}")
            continue

    if reports:
        summary_path = generate_summary_md(reports)
        log.info(f"خلاصه‌ی کل واچ‌لیست: {summary_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="اجرای دستی و سریع بک‌تست")
    parser.add_argument("--symbol", type=str, default=None, help="فقط یک ارز خاص (مثل BTC)")
    parser.add_argument("--coinex-only", action="store_true",
                         help="بدون Yahoo، فقط تاریخچه‌ی کوتاه CoinEx (سریع‌تر، بدون نیاز به calibration)")
    args = parser.parse_args()
    run(symbol_filter=args.symbol, coinex_only=args.coinex_only)
