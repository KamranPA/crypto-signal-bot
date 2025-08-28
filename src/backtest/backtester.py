# src/backtest/backtester.py

import sys
import os
import pandas as pd
import traceback
from importlib import reload  # 🔥 برای بارگذاری مجدد ماژول‌ها

# افزودن مسیر ریشه پروژه به sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# ماژول‌های داخلی — ابتدا وارد کنیم، سپس دوباره بارگذاری کنیم
import src.strategy.trend_strategy
import src.strategy.range_strategy
import src.strategy.breakout_strategy
import src.strategy.trading_system

# 🔁 دوباره بارگذاری ماژول‌ها برای اطمینان از اعمال تغییرات
try:
    reload(src.strategy.trend_strategy)
    reload(src.strategy.range_strategy)
    reload(src.strategy.breakout_strategy)
    reload(src.strategy.trading_system)
    print("✅ ماژول‌های استراتژی با موفقیت دوباره بارگذاری شدند")
except Exception as e:
    print(f"❌ خطا در بارگذاری مجدد ماژول‌ها: {e}")

# حالا وارد کنیم
from src.strategy.trading_system import get_signal
from src.data.data_fetcher import fetch_data
from utils.telegram_notifier import send_telegram_message, send_long_message


def run_backtest(df, strategy_func, initial_capital=1000.0, leverage=10):
    """
    اجرای بک‌تست روی داده‌ها با مدیریت موقعیت، SL/TP و محاسبه سود/ضرر
    """
    print("🔄 شروع اجرای بک‌تست...")
    trades = []
    position = None
    current_capital = initial_capital

    for i in range(50, len(df)):
        window = df.iloc[:i+1].copy()
        signal_result = strategy_func(window)

        if signal_result is None:
            continue

        signal = signal_result.get('signal')
        entry = signal_result.get('entry')
        sl = signal_result.get('stop_loss')
        tp = signal_result.get('take_profit')
        regime = signal_result.get('regime', 'Unknown')

        if entry is None or sl is None or tp is None:
            continue
        if (signal == 'BUY' and (sl >= entry or tp <= entry)) or \
           (signal == 'SELL' and (sl <= entry or tp >= entry)):
            continue

        if signal == 'BUY' and not position:
            position_size = current_capital * leverage
            position = {
                'type': 'long',
                'entry': entry,
                'sl': sl,
                'tp': tp,
                'start_time': window.index[-1],
                'position_size': position_size,
                'regime': regime
            }

        elif signal == 'SELL' and not position:
            position_size = current_capital * leverage
            position = {
                'type': 'short',
                'entry': entry,
                'sl': sl,
                'tp': tp,
                'start_time': window.index[-1],
                'position_size': position_size,
                'regime': regime
            }

        if position:
            current = df.iloc[i]
            exit_price = None
            exit_type = None

            if position['type'] == 'long':
                if current['low'] <= position['sl']:
                    exit_price = position['sl']
                    exit_type = 'SL'
                elif current['high'] >= position['tp']:
                    exit_price = position['tp']
                    exit_type = 'TP'

            elif position['type'] == 'short':
                if current['high'] >= position['sl']:
                    exit_price = position['sl']
                    exit_type = 'SL'
                elif current['low'] <= position['tp']:
                    exit_price = position['tp']
                    exit_type = 'TP'

            if exit_price is not None:
                if position['type'] == 'long':
                    price_change_pct = (exit_price - position['entry']) / position['entry']
                else:
                    price_change_pct = (position['entry'] - exit_price) / position['entry']

                pnl_usd = position['position_size'] * price_change_pct
                current_capital += pnl_usd

                trades.append({
                    'type': position['type'],
                    'entry': position['entry'],
                    'exit': exit_price,
                    'exit_type': exit_type,
                    'start': position['start_time'],
                    'end': current.name,
                    'pnl_percent': round(price_change_pct * 100, 2),
                    'pnl_usd': round(pnl_usd, 2),
                    'capital_after': round(current_capital, 2),
                    'sl': position['sl'],
                    'tp': position['tp'],
                    'regime': position['regime']
                })
                position = None

    total_trades = len(trades)
    winning_trades = len([t for t in trades if t['pnl_usd'] > 0])
    win_rate = round(winning_trades / total_trades * 100, 2) if total_trades > 0 else 0

    capital_curve = [initial_capital] + [t['capital_after'] for t in trades]
    peak = pd.Series(capital_curve).cummax()
    drawdown_pct = ((peak - pd.Series(capital_curve)) / peak) * 100
    max_drawdown = drawdown_pct.max()

    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': total_trades - winning_trades,
        'win_rate': win_rate,
        'drawdown': round(max_drawdown, 2),
        'total_pnl_usd': round(sum(t['pnl_usd'] for t in trades), 2),
        'final_capital': round(current_capital, 2),
        'trades': trades
    }


def format_report(result, symbol, timeframe, start_date, end_date):
    r = result
    report = f"""
🚀 بک‌تست انجام شد!
——————————————
🔹 نماد: {symbol}
🔹 تایم‌فریم: {timeframe}
🔹 دوره: {start_date} تا {end_date}
🔹 سرمایه اولیه: $1000
——————————————
📊 آمار کلی:
• سود/ضرر: ${r['total_pnl_usd']:+.2f}
• سرمایه نهایی: ${r['final_capital']:.2f}
• معاملات: {r['total_trades']} | برد: {r['win_rate']}%
• ضرر حداکثر: {r['drawdown']}%
"""

    if r['total_trades'] == 0:
        report += "\n❌ هیچ سیگنالی تولید نشد."
        return report

    report += "\n\n📌 معاملات:\n"
    for i, t in enumerate(r['trades'], 1):
        side = "🟢 خرید" if t['type'] == 'long' else "🔴 فروش"
        pnl_icon = "✅" if t['pnl_usd'] > 0 else "❌"
        report += (
            f"{i}. {side} | {t['regime']}\n"
            f"   📅 {t['start']} → {t['end']}\n"
            f"   💹 ورود: {t['entry']:.6f}\n"
            f"   🟢 حد سود: {t['tp']:.6f}\n"
            f"   🔴 حد ضرر: {t['sl']:.6f}\n"
            f"   📤 خروج: {t['exit']:.6f} ({t['exit_type']})\n"
            f"   {pnl_icon} سود: ${t['pnl_usd']:+.2f}\n"
            f"   💰 پس از: ${t['capital_after']:.2f}\n\n"
        )
    return report


def main():
    try:
        print("🚀 شروع بک‌تست...")

        # --- دریافت ورودی‌ها از متغیرهای محیطی ---
        symbol_input = os.getenv("SYMBOL", "BTC/USDT")
        timeframe = os.getenv("TIMEFRAME", "1h")
        start_date_str = os.getenv("START_DATE", "2024-05-01")
        end_date_str = os.getenv("END_DATE", "2024-06-01")

        # --- پاک‌سازی نماد ---
        symbol = symbol_input.replace("/", "").strip().upper()  # BTCUSDT
        start_date = pd.to_datetime(start_date_str)
        end_date = pd.to_datetime(end_date_str)

        # --- دریافت داده ---
        print(f"🔄 دریافت داده برای {symbol_input} در تایم‌فریم {timeframe}...")
        df = fetch_data(symbol, timeframe, start_date, end_date)

        if df.empty:
            error_msg = f"❌ داده‌ای برای {symbol_input} در {timeframe} یافت نشد."
            print(error_msg)
            send_telegram_message(error_msg)
            return

        if len(df) < 50:
            error_msg = f"❌ داده کافی برای {symbol_input} در {timeframe} موجود نیست."
            print(error_msg)
            send_telegram_message(error_msg)
            return

        print(f"✅ داده دریافت شد: {len(df)} کندل")

        # --- اجرای بک‌تست ---
        print("🔄 اجرای بک‌تست...")
        result = run_backtest(df, get_signal, initial_capital=1000.0, leverage=10)
        print(f"✅ بک‌تست انجام شد: {result['total_trades']} معامله")

        # --- تولید گزارش ---
        report = format_report(result, symbol_input, timeframe, start_date_str, end_date_str)

        # --- ارسال به تلگرام ---
        print("📤 ارسال گزارش به تلگرام...")
        send_long_message(report)

        # --- پیام خلاصه ---
        summary = (
            f"✅ بک‌تست {symbol_input} | "
            f"معاملات: {result['total_trades']} | "
            f"سود: ${result['total_pnl_usd']:+.2f}"
        )
        send_telegram_message(summary)

        print("🎉 بک‌تست با موفقیت اجرا شد.")

    except Exception as e:
        error_msg = (
            f"❌ خطا در اجرای بک‌تست:\n\n"
            f"<b>نماد:</b> {os.getenv('SYMBOL', 'N/A')}\n"
            f"<b>تایم‌فریم:</b> {os.getenv('TIMEFRAME', 'N/A')}\n"
            f"<b>خطا:</b> {str(e)}\n\n"
            f"<pre>{traceback.format_exc()}</pre>"
        )
        print(f"❌ خطا: {e}")
        send_telegram_message(error_msg)


# اجرای برنامه وقتی فایل مستقیماً اجرا شود
if __name__ == "__main__":
    main()
