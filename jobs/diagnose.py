# مسیر فایل: jobs/diagnose.py
"""
اسکریپت تشخیصی — برای فهمیدن این‌که چرا سیگنالی به تلگرام نرسیده، بدون نیاز به
کندوکاو دستی در لاگ‌های GitHub Actions.

برای هر ارز واچ‌لیست (یا فقط یک ارز با --symbol) نشان می‌دهد:
  - آیا اتصال به CoinEx برقرار است و کندل آخر چه زمانی است
  - مقدار فعلی Supertrend / ADX / Close و فاصله‌شان تا آستانه
  - آیا در همین کندل bull/bear فعال شده یا نه، و اگر نه، دقیقاً کدام شرط رد شده
  - آیا مدل ML و پارامتر فعال (از Supabase) موجود است یا از baseline استفاده می‌شود
  - تست WRITE واقعی روی Supabase (insert + delete) — جدا از تست خواندن
  - تست اتصال تلگرام (بدون ارسال سیگنال واقعی، فقط پیام تشخیصی)

استفاده:
    python -m jobs.diagnose                  # همه‌ی واچ‌لیست
    python -m jobs.diagnose --symbol BTC      # فقط یک ارز
    python -m jobs.diagnose --test-telegram   # + ارسال یک پیام تست به تلگرام
    python -m jobs.diagnose --history         # + آخرین باری که هر ارز واقعاً سیگنال داده
    python -m jobs.diagnose --skip-write-test # رد کردن تست نوشتن Supabase
"""
from __future__ import annotations
import argparse
import os
import yaml
from pathlib import Path

from data.coinex_client import fetch_latest_candle
from strategy.core import generate_raw_signals
from ml.predict import load_latest_model

ROOT = Path(__file__).resolve().parent.parent


def load_config():
    watchlist = yaml.safe_load((ROOT / "config/watchlist.yaml").read_text(encoding="utf-8"))
    params_default = yaml.safe_load((ROOT / "config/params_default.yaml").read_text(encoding="utf-8"))
    return watchlist, params_default


def check_env_vars():
    print("=" * 60)
    print("STEP 1: environment variables check")
    print("=" * 60)
    required = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "SUPABASE_URL", "SUPABASE_KEY"]
    all_ok = True
    for var in required:
        present = bool(os.environ.get(var))
        status = "✅ موجود" if present else "❌ خالی/موجود نیست"
        print(f"  {var}: {status}")
        all_ok = all_ok and present
    if not all_ok:
        print("  ⚠️  اگر این اسکریپت را در GitHub Actions اجرا می‌کنید و اینجا خالی می‌بینید،")
        print("      یعنی Secrets در تنظیمات ریپو درست ثبت نشده یا در workflow پاس داده نشده.")
    print()
    return all_ok


def try_get_active_params(symbol_name):
    try:
        from storage.supabase_client import get_client, get_active_params
        client = get_client()
        return get_active_params(client, symbol_name)
    except Exception as e:
        print(f"  ⚠️  اتصال به Supabase ناموفق بود: {e}")
        return None


def diagnose_symbol(coin, params_default, timeframe):
    symbol_name = coin["name"]
    print("-" * 60)
    print(f"ارز: {symbol_name}")
    print("-" * 60)

    try:
        df = fetch_latest_candle(coin["coinex_symbol"], timeframe)
    except Exception as e:
        print(f"  ❌ خطا در دریافت دیتا از CoinEx: {e}")
        return

    print(f"  آخرین کندل: {df.index[-1]} | close={df['close'].iloc[-1]:.4f}")

    d = generate_raw_signals(df, params_default)
    last = d.iloc[-1]
    adx_threshold = params_default["indicator"]["adx_threshold"]

    cross_over = (d["close"].shift(1) <= d["supertrend"].shift(1)).iloc[-1] and (last["close"] > last["supertrend"])
    cross_under = (d["close"].shift(1) >= d["supertrend"].shift(1)).iloc[-1] and (last["close"] < last["supertrend"])

    print(f"  Supertrend: {last['supertrend']:.4f} | Close: {last['close']:.4f}")
    print(f"  ADX: {last['adx']:.2f} (آستانه: {adx_threshold}) → "
          f"{'✅ بالای آستانه' if last['adx'] > adx_threshold else '❌ زیر آستانه (سیگنال رد می‌شود)'}")
    print(f"  Crossover صعودی این کندل: {'✅ بله' if cross_over else '❌ خیر'}")
    print(f"  Crossunder نزولی این کندل: {'✅ بله' if cross_under else '❌ خیر'}")
    print(f"  نتیجه‌ی نهایی bull: {bool(last.get('bull'))} | bear: {bool(last.get('bear'))}")

    if not (last.get("bull") or last.get("bear")):
        print("  ℹ️  در این کندل سیگنالی صادر نمی‌شود (طبیعی است — سیگنال فقط گاه‌به‌گاه رخ می‌دهد،")
        print("      نه هر ساعت. برای دیدن آخرین کندلی که سیگنال داده، --history را اضافه کنید.)")

    active = try_get_active_params(symbol_name)
    if active:
        print(f"  پارامتر فعال از Supabase: نسخه {active['version']} "
              f"(ATR×{active['atr_mult']}, آستانه ML={active['ml_threshold']})")
    else:
        print("  پارامتر فعال در Supabase یافت نشد → از baseline استفاده می‌شود "
              f"(ATR×{params_default['risk_defaults']['atr_mult']}, "
              f"آستانه ML={params_default['ml_defaults']['confidence_threshold']})")

    model = load_latest_model(symbol_name)
    print(f"  مدل ML: {'موجود' if model else '❌ هنوز train نشده (فیلتری اعمال نمی‌شود، فقط rule-based)'}")
    print()


def find_last_signal(coin, params_default, timeframe, lookback_bars: int = 500):
    """کمک‌کننده: آخرین باری که این ارز واقعاً سیگنال داده کِی بوده."""
    from data.coinex_client import fetch_ohlcv
    df = fetch_ohlcv(coin["coinex_symbol"], timeframe, limit=lookback_bars)
    d = generate_raw_signals(df, params_default)
    signals = d[d["bull"] | d["bear"]]
    if signals.empty:
        print(f"  در {lookback_bars} کندل اخیر هیچ سیگنالی صادر نشده.")
    else:
        last_sig = signals.iloc[-1]
        direction = "bull" if last_sig["bull"] else "bear"
        print(f"  آخرین سیگنال واقعی: {signals.index[-1]} ({direction}) "
              f"— {len(signals)} سیگنال در {lookback_bars} کندل اخیر")


def test_supabase_write():
    print("=" * 60)
    print("STEP 3: Supabase WRITE test (insert + delete round trip)")
    print("=" * 60)
    try:
        from storage.supabase_client import get_client
        from datetime import datetime, timezone
        client = get_client()

        test_symbol = "__DIAGNOSTIC_TEST__"
        test_row = {
            "symbol": test_symbol, "timeframe": "1h",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0,
            "volume": 1.0, "source": "diagnostic",
        }

        try:
            client.table("ohlcv_cache").insert(test_row).execute()
            print("  INSERT: OK")
        except Exception as e:
            print(f"  INSERT: FAILED -> {e}")
            print("  LIKELY CAUSE: Row Level Security (RLS) is enabled on this table")
            print("  without a policy allowing INSERT for the key you are using.")
            print("  Fix in Supabase SQL Editor:")
            print("    alter table ohlcv_cache disable row level security;")
            print("    alter table signals disable row level security;")
            print("    alter table model_registry disable row level security;")
            print("    alter table param_history disable row level security;")
            print("    alter table backtest_runs disable row level security;")
            return

        try:
            client.table("ohlcv_cache").delete().eq("symbol", test_symbol).execute()
            print("  DELETE (cleanup): OK")
        except Exception as e:
            print(f"  DELETE (cleanup) FAILED -- test row '{test_symbol}' may remain in ohlcv_cache: {e}")

        print("  RESULT: Supabase read AND write both work correctly.")

    except Exception as e:
        print(f"  Could not even initialize Supabase client: {e}")
    print()


def test_telegram():
    print("=" * 60)
    print("تست ارسال پیام تشخیصی به تلگرام")
    print("=" * 60)
    try:
        from notify.telegram_bot import send_text
        send_text("🔧 پیام تشخیصی از jobs/diagnose.py — اگر این را می‌بینید، اتصال تلگرام سالم است.")
        print("  ✅ پیام ارسال شد — تلگرام خود را چک کنید.")
    except Exception as e:
        print(f"  ❌ ارسال ناموفق: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="تشخیص علت عدم ارسال سیگنال")
    parser.add_argument("--symbol", type=str, default=None)
    parser.add_argument("--test-telegram", action="store_true")
    parser.add_argument("--history", action="store_true",
                         help="نمایش آخرین باری که هر ارز واقعاً سیگنال داده")
    parser.add_argument("--skip-write-test", action="store_true",
                         help="رد کردن تست نوشتن در Supabase")
    args = parser.parse_args()

    watchlist, params_default = load_config()
    check_env_vars()

    print("=" * 60)
    print("STEP 2: signal status per coin")
    print("=" * 60)
    for coin in watchlist["coins"]:
        if args.symbol and coin["name"] != args.symbol:
            continue
        diagnose_symbol(coin, params_default, watchlist["timeframe"])
        if args.history:
            try:
                find_last_signal(coin, params_default, watchlist["timeframe"])
            except Exception as e:
                print(f"  ERROR in find_last_signal: {e}")
            print()

    if not args.skip_write_test:
        test_supabase_write()

    if args.test_telegram:
        test_telegram()
