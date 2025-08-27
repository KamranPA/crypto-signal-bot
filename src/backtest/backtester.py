# src/backtest/backtester.py

import sys
import os
import pandas as pd
import traceback

# افزودن مسیر ریشه پروژه
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ماژول‌های داخلی
from data.data_fetcher import fetch_data
from strategy.trading_system import get_signal
from utils.telegram_notifier import send_telegram_message, send_long_message


def run_backtest(df, strategy_func, initial_capital=1000.0, leverage=10):
    """
    اجرای بک‌تست با دیباگ گام‌به‌گام
    """
    print("🔄 شروع بک‌تست با دیباگ...")
    trades = []
    position = None
    current_capital = initial_capital

    for i in range(50, len(df)):
        print(f"\n🔍 مرحله {i}: بررسی کندل {df.index[i]}")

        # --- 1. ساخت پنجره ---
        try:
            window = df.iloc[:i+1].copy()
            print(f"   ✅ پنجره ساخته شد: {len(window)} کندل")
        except Exception as e:
            print(f"   ❌ خطا در ساخت پنجره: {e}")
            continue

        # --- 2. فراخوانی استراتژی ---
        try:
            signal_result = strategy_func(window)
            print(f"   📢 خروجی get_signal: {signal_result}")
        except Exception as e:
            print(f"   ❌ خطا در get_signal: {e}")
            traceback.print_exc()
            continue

        # --- 3. بررسی سیگنال ---
        if signal_result is None:
            print("   ⚠️  سیگنال تولید نشد (None)")
            continue

        if not isinstance(signal_result, dict):
            print(f"   ❌ خروجی get_signal یک دیکشنری نیست: {type(signal_result)}")
            continue

        # --- 4. استخراج مقادیر ---
        try:
            signal = signal_result.get('signal')
            entry = signal_result.get('entry')
            sl = signal_result.get('stop_loss')
            tp = signal_result.get('take_profit')
            regime = signal_result.get('regime', 'Unknown')

            print(f"   📌 سیگنال: {signal} | ورود: {entry} | حد ضرر: {sl} | حد سود: {tp}")

            # --- فیلتر مقادیر ---
            if entry is None or sl is None or tp is None:
                print(f"   ❌ ورود/حد ضرر/حد سود None است: entry={entry}, sl={sl}, tp={tp}")
                continue

            if (signal == 'BUY' and (sl >= entry or tp <= entry)) or \
               (signal == 'SELL' and (sl <= entry or tp >= entry)):
                print("   ❌ حد ضرر/سود نامعتبر است (SL >= Entry یا TP <= Entry)")
                continue

        except Exception as e:
            print(f"   ❌ خطا در استخراج مقادیر سیگنال: {e}")
            traceback.print_exc()
            continue

        # --- 5. ورود به معامله ---
        try:
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
                print(f"   🟢 ورود خرید: ورود={entry}, SL={sl}, TP={tp}")

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
                print(f"   🔴 ورود فروش: ورود={entry}, SL={sl}, TP={tp}")

        except Exception as e:
            print(f"   ❌ خطا در ایجاد موقعیت: {e}")
            traceback.print_exc()
            continue

        # --- 6. خروج از معامله ---
        if position:
            current = df.iloc[i]
            exit_price = None
            exit_type = None

            try:
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
                    print(f"   ✅ خروج: {exit_type} در {exit_price} | سود: ${pnl_usd:+.2f}")
                    position = None

            except Exception as e:
                print(f"   ❌ خطا در مدیریت خروج: {e}")
                traceback.print_exc()

    # --- محاسبه آمار ---
    total_trades = len(trades)
    winning_trades = len([t for t in trades if t['pnl_usd'] > 0])
    win_rate = round(winning_trades / total_trades * 100, 2) if total_trades > 0 else 0

    capital_curve = [initial_capital] + [t['capital_after'] for t in trades]
    peak = pd.Series(capital_curve).cummax()
    drawdown = ((peak - pd.Series(capital_curve)) / peak) * 100
    max_drawdown = drawdown.max()

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
        symbol_input = os.getenv("SYMBOL", "BTC/USDT")
        timeframe = os.getenv("TIMEFRAME", "1h")
        start_date_str = os.getenv("START_DATE", "2024-05-01")
        end_date_str = os.getenv("END_DATE", "2024-06-01")

        symbol = symbol_input.replace("/", "").upper()
        start_date = pd.to_datetime(start_date_str)
        end_date = pd.to_datetime(end_date_str)

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
        result = run_backtest(df, get_signal)
        report = format_report(result, symbol_input, timeframe, start_date_str, end_date_str)
        send_long_message(report)

        summary = f"✅ بک‌تست {symbol_input} | معاملات: {result['total_trades']} | سود: ${result['total_pnl_usd']:+.2f}"
        send_telegram_message(summary)

    except Exception as e:
        error = f"❌ خطا:\n\n{str(e)}\n\n<pre>{traceback.format_exc()}</pre>"
        send_telegram_message(error)


if __name__ == "__main__":
    main()
