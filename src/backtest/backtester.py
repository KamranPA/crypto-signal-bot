# src/backtest/backtester.py

import sys
import os
import pandas as pd

# 🔧 اضافه کردن مسیر src به sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

# ✅ ایمپورت ماژول‌ها
from src.strategy.trading_system import get_signal
from src.data.data_fetcher import fetch_data
from src.utils.telegram_notifier import send_telegram_message

def run_backtest(df, initial_capital=1000.0, leverage=10):
    trades = []
    position = None
    current_capital = initial_capital

    for i in range(50, len(df)):
        window = df.iloc[:i+1].copy()
        signal_result = get_signal(window)
        if not signal_result:
            continue

        entry = signal_result.get('entry')
        sl = signal_result.get('stop_loss')
        tp = signal_result.get('take_profit')
        if any(x is None for x in [entry, sl, tp]):
            continue
        if (signal_result['signal'] == 'BUY' and (sl >= entry or tp <= entry)) or \
           (signal_result['signal'] == 'SELL' and (sl <= entry or tp >= entry)):
            continue

        if signal_result['signal'] == 'BUY' and not position:
            position = {
                'type': 'long',
                'entry': entry,
                'sl': sl,
                'tp': tp,
                'start_time': window.index[-1],
                'position_size': current_capital * leverage,
                'regime': signal_result.get('regime', 'Unknown')
            }
        elif signal_result['signal'] == 'SELL' and not position:
            position = {
                'type': 'short',
                'entry': entry,
                'sl': sl,
                'tp': tp,
                'start_time': window.index[-1],
                'position_size': current_capital * leverage,
                'regime': signal_result.get('regime', 'Unknown')
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
            else:
                if current['high'] >= position['sl']:
                    exit_price = position['sl']
                    exit_type = 'SL'
                elif current['low'] <= position['tp']:
                    exit_price = position['tp']
                    exit_type = 'TP'

            if exit_price is not None:
                pnl = (exit_price - position['entry']) / position['entry'] if position['type'] == 'long' \
                    else (position['entry'] - exit_price) / position['entry']
                pnl_usd = position['position_size'] * pnl
                current_capital += pnl_usd

                trades.append({
                    'type': position['type'],
                    'entry': position['entry'],
                    'exit': exit_price,
                    'exit_type': exit_type,
                    'start': position['start_time'],
                    'end': current.name,
                    'pnl_percent': round(pnl * 100, 2),
                    'pnl_usd': round(pnl_usd, 2),
                    'capital_after': round(current_capital, 2),
                    'regime': position['regime']
                })
                position = None

    total = len(trades)
    wins = len([t for t in trades if t['pnl_usd'] > 0])
    win_rate = round(wins / total * 100, 2) if total > 0 else 0
    dd_curve = [initial_capital] + [t['capital_after'] for t in trades]
    peak = pd.Series(dd_curve).cummax()
    drawdown = ((peak - pd.Series(dd_curve)) / peak) * 100
    max_dd = drawdown.max()

    return {
        'total_trades': total,
        'winning_trades': wins,
        'losing_trades': total - wins,
        'win_rate': win_rate,
        'drawdown': round(max_dd, 2),
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
        report += (f"{i}. {side} | {t['regime']}\n"
                   f"   📅 {t['start']} → {t['end']}\n"
                   f"   💹 ورود: {t['entry']:.6f}\n"
                   f"   🟢 حد سود: {t['tp']:.6f}\n"
                   f"   🔴 حد ضرر: {t['sl']:.6f}\n"
                   f"   📤 خروج: {t['exit']:.6f} ({t['exit_type']})\n"
                   f"   {pnl_icon} سود: ${t['pnl_usd']:+.2f}\n"
                   f"   💰 پس از: ${t['capital_after']:.2f}\n\n")
    return report


def main():
    try:
        symbol = os.getenv("SYMBOL", "BTC/USDT")
        timeframe = os.getenv("TIMEFRAME", "1h")
        start_date_str = os.getenv("START_DATE", "2024-05-01")
        end_date_str = os.getenv("END_DATE", "2024-08-21")  # ✅ همیشه قبل از امروز

        start_date = pd.to_datetime(start_date_str)
        end_date = min(pd.to_datetime(end_date_str), pd.to_datetime("today"))

        df = fetch_data(symbol, timeframe, start_date, end_date)
        if df.empty:
            msg = f"❌ داده‌ای برای {symbol} در {timeframe} یافت نشد."
            print(msg)
            send_telegram_message(msg)
            return

        result = run_backtest(df)
        report = format_report(result, symbol, timeframe, start_date_str, end_date_str)
        send_telegram_message(report)

        summary = f"✅ بک‌تست {symbol} | معاملات: {result['total_trades']} | سود: ${result['total_pnl_usd']:+.2f}"
        send_telegram_message(summary)
        print("🎉 بک‌تست با موفقیت اجرا شد.")

    except Exception as e:
        error_msg = f"❌ خطا در اجرای بک‌تست:\n<pre>{str(e)}</pre>"
        send_telegram_message(error_msg)
        print(f"❌ خطا: {e}")


if __name__ == "__main__":
    main()
