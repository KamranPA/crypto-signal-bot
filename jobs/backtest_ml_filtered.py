# مسیر فایل: jobs/backtest_ml_filtered.py
"""
اجرای بک‌تست «کل سیستم» (rule-based + فیلتر واقعی ML) — فقط روی بخش انتهایی داده
(همان test split که مدل موقع آموزش ندیده) تا نتیجه منصفانه و بدون look-ahead باشد.

استفاده:
    python -m jobs.backtest_ml_filtered                  # همه‌ی واچ‌لیست
    python -m jobs.backtest_ml_filtered --symbol BTC      # فقط یک ارز
    python -m jobs.backtest_ml_filtered --coinex-only     # سریع‌تر، بدون Yahoo
"""
from __future__ import annotations
import argparse
import logging
import yaml
from pathlib import Path

from data.coinex_client import fetch_ohlcv as coinex_fetch
from data.yahoo_client import fetch_ohlcv as yahoo_fetch
from data.calibration import build_calibrated_history
from ml.predict import load_latest_model
from backtest.ml_filtered import run_ml_filtered_backtest, print_comparison

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("backtest_ml_filtered")

ROOT = Path(__file__).resolve().parent.parent


def load_config():
    watchlist = yaml.safe_load((ROOT / "config/watchlist.yaml").read_text(encoding="utf-8"))
    params_default = yaml.safe_load((ROOT / "config/params_default.yaml").read_text(encoding="utf-8"))
    return watchlist, params_default


def get_active_params_safe(symbol: str, params_default: dict) -> dict:
    try:
        from storage.supabase_client import get_client, get_active_params
        client = get_client()
        active = get_active_params(client, symbol)
        if active:
            return active
    except Exception as e:
        log.warning(f"{symbol}: Supabase در دسترس نیست ({e})، از baseline استفاده می‌شود.")
    return None


def run(symbol_filter: str | None = None, coinex_only: bool = False):
    watchlist, params_default = load_config()

    for coin in watchlist["coins"]:
        symbol_name = coin["name"]
        if symbol_filter and symbol_name != symbol_filter:
            continue

        log.info(f"=== {symbol_name} ===")
        try:
            model = load_latest_model(symbol_name)
            if model is None:
                log.warning(f"{symbol_name}: مدل ML موجود نیست — رد شد (این تحلیل بدون مدل معنا ندارد).")
                continue

            active = get_active_params_safe(symbol_name, params_default)
            if active:
                risk_params = {
                    "atr_mult": active["atr_mult"], "tp1_r": active["tp1_r"],
                    "tp2_r": active["tp2_r"], "tp3_r": active["tp3_r"],
                }
                ml_threshold = active["ml_threshold"]
            else:
                risk_params = params_default["risk_defaults"]
                ml_threshold = params_default["ml_defaults"]["confidence_threshold"]

            df_coinex = coinex_fetch(coin["coinex_symbol"], watchlist["timeframe"])
            if coinex_only:
                df = df_coinex
            else:
                df_yahoo = yahoo_fetch(coin["yahoo_symbol"],
                                        period=f"{watchlist['backtest_years']*365}d", interval="1h")
                df = build_calibrated_history(df_yahoo, df_coinex)

            full_report, filtered_report = run_ml_filtered_backtest(
                df, symbol_name, params_default, risk_params, model, ml_threshold, test_only=True
            )
            print_comparison(symbol_name, full_report, filtered_report)

        except Exception as e:
            log.exception(f"خطا در {symbol_name}: {e}")
            continue


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="بک‌تست rule-based در برابر فیلترشده‌ی ML")
    parser.add_argument("--symbol", type=str, default=None)
    parser.add_argument("--coinex-only", action="store_true")
    args = parser.parse_args()
    run(symbol_filter=args.symbol, coinex_only=args.coinex_only)
