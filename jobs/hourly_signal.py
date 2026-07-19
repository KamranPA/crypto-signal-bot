# مسیر فایل: jobs/hourly_signal.py
"""
اسکریپت اجرای ساعتی — توسط .github/workflows/hourly_signal.yml اجرا می‌شود.

مراحل:
  ۱. برای هر ارز واچ‌لیست: دریافت کندل‌های اخیر از CoinEx
  ۲. محاسبه‌ی اندیکاتورها + تولید سیگنال rule-based (strategy/core.py)
  ۳. اگر سیگنال جدید بود: فیلتر ML (ml/predict.py) با آستانه‌ی فعال آن ارز
  ۴. در صورت تأیید: ارسال تلگرام + ذخیره در Supabase (جدول signals)
     در صورت رد شدن توسط ML: ذخیره در جدول rejected_signals (برای تحلیل بعدی آستانه)
  ۵. بررسی معاملات pending قبلی: آیا TP/SL لمس شده؟ (به‌روزرسانی وضعیت)

نکته‌ی مهم: ارسال تلگرام هرگز نباید به موفقیت Supabase وابسته باشد. هر تعامل با
Supabase جداگانه در try/except محافظت شده — اگر Supabase fail شود فقط warning
چاپ می‌شود و مسیر اصلی (سیگنال → تلگرام) ادامه پیدا می‌کند.

نکته‌ی دوم: وقتی مدل ML هنوز train نشده، confidence مقدار None است (نه ۱۰۰٪ ساختگی)
تا در پیام تلگرام و لاگ‌ها با یک امتیاز واقعی مدل اشتباه گرفته نشود.
"""
from __future__ import annotations
import logging
import yaml
from pathlib import Path

from data.coinex_client import fetch_latest_candle
from strategy.core import generate_raw_signals, build_signal
from ml.predict import load_latest_model, is_signal_confirmed
from notify.telegram_bot import send_signal
from storage.supabase_client import (
    get_client, insert_signal, insert_rejected_signal, cache_ohlcv,
    get_active_params, get_pending_signals, update_signal_status,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("hourly_signal")

ROOT = Path(__file__).resolve().parent.parent


def load_config():
    watchlist = yaml.safe_load((ROOT / "config/watchlist.yaml").read_text(encoding="utf-8"))
    params_default = yaml.safe_load((ROOT / "config/params_default.yaml").read_text(encoding="utf-8"))
    return watchlist, params_default


def check_pending_outcomes(client, symbol: str, df_with_indicators):
    """بررسی می‌کند آیا معاملات pending این ارز به TP/SL رسیده‌اند (برای حلقه‌ی یادگیری)."""
    pending = get_pending_signals(client, symbol)
    last_row = df_with_indicators.iloc[-1]
    for p in pending:
        direction = p["direction"]
        if direction == "bull":
            if last_row["low"] <= p["stop_loss"]:
                pnl = (p["stop_loss"] - p["entry"]) / p["entry"] * 100
                update_signal_status(client, p["id"], "sl_hit", pnl)
            elif last_row["high"] >= p["tp3"]:
                pnl = (p["tp3"] - p["entry"]) / p["entry"] * 100
                update_signal_status(client, p["id"], "tp3_hit", pnl)
        else:
            if last_row["high"] >= p["stop_loss"]:
                pnl = (p["entry"] - p["stop_loss"]) / p["entry"] * 100
                update_signal_status(client, p["id"], "sl_hit", pnl)
            elif last_row["low"] <= p["tp3"]:
                pnl = (p["entry"] - p["tp3"]) / p["entry"] * 100
                update_signal_status(client, p["id"], "tp3_hit", pnl)


def safe_cache_ohlcv(client, symbol_name, timeframe, df_tail):
    """ذخیره در Supabase — اگر fail شود فقط warning می‌دهد، جریان اصلی متوقف نمی‌شود."""
    try:
        cache_ohlcv(client, symbol_name, timeframe, df_tail)
    except Exception as e:
        log.warning(f"{symbol_name}: cache_ohlcv failed (non-fatal): {e}")


def safe_get_active_params(client, symbol_name):
    try:
        return get_active_params(client, symbol_name)
    except Exception as e:
        log.warning(f"{symbol_name}: get_active_params failed, using baseline (non-fatal): {e}")
        return None


def safe_check_pending_outcomes(client, symbol_name, d):
    try:
        check_pending_outcomes(client, symbol_name, d)
    except Exception as e:
        log.warning(f"{symbol_name}: check_pending_outcomes failed (non-fatal): {e}")


def safe_insert_signal(client, sig, confidence, version):
    try:
        insert_signal(client, sig, confidence, version)
    except Exception as e:
        log.warning(f"{sig.symbol}: insert_signal failed — signal WAS sent to Telegram "
                    f"but NOT recorded in Supabase (non-fatal): {e}")


def safe_insert_rejected_signal(client, sig, confidence, threshold):
    try:
        insert_rejected_signal(client, sig, confidence, threshold)
    except Exception as e:
        log.warning(f"{sig.symbol}: insert_rejected_signal failed (non-fatal): {e}")


def run():
    watchlist, params_default = load_config()

    try:
        client = get_client()
    except Exception as e:
        log.warning(f"Supabase client init failed — continuing WITHOUT storage this run: {e}")
        client = None

    for coin in watchlist["coins"]:
        symbol_name = coin["name"]
        coinex_symbol = coin["coinex_symbol"]
        log.info(f"Processing {symbol_name}...")

        try:
            df = fetch_latest_candle(coinex_symbol, watchlist["timeframe"])

            active = None
            if client is not None:
                safe_cache_ohlcv(client, symbol_name, watchlist["timeframe"], df.tail(5))
                active = safe_get_active_params(client, symbol_name)

            risk_params = {
                "atr_mult": active["atr_mult"] if active else params_default["risk_defaults"]["atr_mult"],
                "tp1_r": active["tp1_r"] if active else params_default["risk_defaults"]["tp1_r"],
                "tp2_r": active["tp2_r"] if active else params_default["risk_defaults"]["tp2_r"],
                "tp3_r": active["tp3_r"] if active else params_default["risk_defaults"]["tp3_r"],
            }
            ml_threshold = active["ml_threshold"] if active else params_default["ml_defaults"]["confidence_threshold"]

            d = generate_raw_signals(df, params_default)

            if client is not None:
                safe_check_pending_outcomes(client, symbol_name, d)

            last_idx = len(d) - 1
            last_row = d.iloc[last_idx]

            if last_row.get("bull") or last_row.get("bear"):
                sig = build_signal(d, last_idx, symbol_name, risk_params)
                if sig is not None:
                    model = load_latest_model(symbol_name)
                    confirmed, confidence = is_signal_confirmed(model, d, last_idx, ml_threshold)
                    if confirmed:
                        version = active["version"] if active else "baseline"
                        # اولویت با ارسال تلگرام است — این هیچ‌وقت نباید به‌خاطر Supabase قفل شود
                        send_signal(sig, confidence)
                        conf_str = f"{confidence:.2f}" if confidence is not None else "N/A (no ML model yet)"
                        log.info(f"Signal sent: {symbol_name} {sig.direction} (confidence={conf_str})")
                        if client is not None:
                            safe_insert_signal(client, sig, confidence, version)
                    else:
                        log.info(f"Signal rejected by ML filter: {symbol_name} "
                                 f"(confidence={confidence:.2f} < {ml_threshold})")
                        if client is not None:
                            safe_insert_rejected_signal(client, sig, confidence, ml_threshold)
            else:
                log.info(f"No signal for {symbol_name} this bar.")

        except Exception as e:
            log.exception(f"Error processing {symbol_name}: {e}")
            continue


if __name__ == "__main__":
    run()
