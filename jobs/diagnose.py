# مسیر فایل: jobs/diagnose.py
"""
اسکریپت تشخیصی — برای فهمیدن این‌که چرا سیگنالی به تلگرام نرسیده، بدون نیاز به
کندوکاو دستی در لاگ‌های GitHub Actions.

استفاده:
    python -m jobs.diagnose                  # همه‌ی واچ‌لیست
    python -m jobs.diagnose --symbol BTC      # فقط یک ارز
    python -m jobs.diagnose --test-telegram   # + ارسال یک پیام تست به تلگرام
    python -m jobs.diagnose --history         # + آخرین باری که هر ارز واقعاً سیگنال داده
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
        status = "OK - present" if present else "MISSING"
        print(f"  {var}: {status}")
        all_ok = all_ok and present
    if not all_ok:
        print("  WARNING: if running in GitHub Actions and this is empty, check repo Secrets.")
    print()
    return all_ok


def try_get_active_params(symbol_name):
    try:
        from storage.supabase_client import get_client, get_active_params
        client = get_client()
        return get_active_params(client, symbol_name)
    except Exception as e:
        print(f"  WARNING: Supabase connection failed: {e}")
        return None


def diagnose_symbol(coin, params_default, timeframe):
    symbol_name = coin["name"]
    print("-" * 60)
    print(f"Symbol: {symbol_name}")
    print("-" * 60)

    try:
        df = fetch_latest_candle(coin["coinex_symbol"], timeframe)
    except Exception as e:
        print(f"  ERROR fetching CoinEx data: {e}")
        return

    print(f"  Last candle: {df.index[-1]} | close={df['close'].iloc[-1]:.4f}")

    d = generate_raw_signals(df, params_default)
    last = d.iloc[-1]
    adx_threshold = params_default["indicator"]["adx_threshold"]

    cross_over = (d["close"].shift(1) <= d["supertrend"].shift(1)).iloc[-1] and (last["close"] > last["supertrend"])
    cross_under = (d["close"].shift(1) >= d["supertrend"].shift(1)).iloc[-1] and (last["close"] < last["supertrend"])

    print(f"  Supertrend: {last['supertrend']:.4f} | Close: {last['close']:.4f}")
    above = last["adx"] > adx_threshold
    print(f"  ADX: {last['adx']:.2f} (threshold: {adx_threshold}) -> "
          f"{'PASS (above threshold)' if above else 'BLOCKED (below threshold)'}")
    print(f"  Bullish crossover this candle: {'YES' if cross_over else 'no'}")
    print(f"  Bearish crossunder this candle: {'YES' if cross_under else 'no'}")
    print(f"  Final result -> bull: {bool(last.get('bull'))} | bear: {bool(last.get('bear'))}")

    if not (last.get("bull") or last.get("bear")):
        print("  INFO: no signal on this candle (normal - signals are infrequent, not hourly).")
        print("        Use --history to see the last time this coin actually signaled.")

    active = try_get_active_params(symbol_name)
    if active:
        print(f"  Active Supabase params: version {active['version']} "
              f"(ATR x{active['atr_mult']}, ML threshold={active['ml_threshold']})")
    else:
        print("  No active params in Supabase -> using baseline "
              f"(ATR x{params_default['risk_defaults']['atr_mult']}, "
              f"ML threshold={params_default['ml_defaults']['confidence_threshold']})")

    model = load_latest_model(symbol_name)
    print(f"  ML model: {'found' if model else 'NOT TRAINED YET (no filtering applied, rule-based only)'}")
    print()


def find_last_signal(coin, params_default, timeframe, lookback_bars: int = 500):
    """Helper: when this coin last actually produced a signal."""
    from data.coinex_client import fetch_ohlcv
    df = fetch_ohlcv(coin["coinex_symbol"], timeframe, limit=lookback_bars)
    d = generate_raw_signals(df, params_default)
    signals = d[d["bull"] | d["bear"]]
    if signals.empty:
        print(f"  No signal in the last {lookback_bars} bars.")
    else:
        last_sig = signals.iloc[-1]
        direction = "bull" if last_sig["bull"] else "bear"
        print(f"  Last real signal: {signals.index[-1]} ({direction}) "
              f"-- {len(signals)} signals in the last {lookback_bars} bars")


def test_telegram():
    print("=" * 60)
    print("Telegram connectivity test")
    print("=" * 60)
    try:
        from notify.telegram_bot import send_text
        send_text("Diagnostic message from jobs/diagnose.py -- if you see this, Telegram is working.")
        print("  OK: message sent, check your Telegram.")
    except Exception as e:
        print(f"  FAILED to send: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnose why no signal has been sent")
    parser.add_argument("--symbol", type=str, default=None)
    parser.add_argument("--test-telegram", action="store_true")
    parser.add_argument("--history", action="store_true",
                         help="Show the last time each coin actually produced a signal")
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
            find_last_signal(coin, params_default, watchlist["timeframe"])
            print()

    if args.test_telegram:
        test_telegram()
