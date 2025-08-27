# src/backtest/backtester.py

import sys
import os
import pandas as pd
import traceback

# --- اضافه کردن مسیر ریشه پروژه به sys.path ---
# این کار به ما اجازه می‌دهد از ماژول‌ها بدون پیشوند 'src' استفاده کنیم
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- ماژول‌های داخلی ---
from data.data_fetcher import fetch_data
from strategy.trading_system import get_signal
from utils.telegram_notifier import send_telegram_message


def run_backtest(df, strategy_func, initial_capital=1000.0, leverage=10):
    """
    اجرای بک‌تست روی داده‌ها با مدیریت موقعیت، SL/TP و محاسبه سود/ضرر
    """
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

        # فیلتر مقادیر نامعتبر
        if entry is None or sl is None or tp is None:
            continue
        if (signal == 'BUY' and (sl >= entry or tp <= entry or sl >= tp)) or \
           (signal == 'SELL' and (sl <= entry or tp >= entry or sl <= tp)):
            continue

        # ورود به معامله خرید
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

        # ورود به معامله فروش
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

        # بررسی خروج از معامله
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

            # اگر خروج اتفاق افتاد
            if exit_price is not None:
                # محاسبه تغییر قیمت
                if position['type'] == 'long':
                    price_change_pct = (exit_price - position['entry']) / position['entry']
                else:
                    price_change_pct = (position['entry'] - exit_price) / position['entry']

                # محاسبه سود/ضرر
                pnl_usd = position['position_size'] * price_change_pct
                current_capital += pnl_usd

                # ذخیره معامله
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

    # محاسبه آمار نهایی
    total_pnl_usd = sum(t['pnl_usd'] for t in trades)
    total_trades = len(trades)
    winning_trades = len([t for t in trades if t['pnl_usd'] > 0])
    win_rate = round(winning_trades / total_trades * 100, 2) if total_trades > 0 else 0

    # محاسبه ضرر حداکثر (Max Drawdown)
    capital_curve = [initial_capital] + [t['capital_after'] for t in trades]
    peak = pd.Series(capital_curve).cummax()
    drawdown_pct = ((peak - pd.Series(capital_curve)) / peak) * 100
    max_drawdown = drawdown_pct.max()

    # بازگشت نتیجه
    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': total_trades - winning_trades,
        'win_rate': win_rate,
        'drawdown': round(max_drawdown, 2),
        'total_pnl_usd': round(total_pnl_usd, 2),
        'final_capital': round(current_capital, 2),
        'trades': trades
    }


def format_report(result, symbol, timeframe, start_date, end_date):
    """تولید گزارش زیبا برای ارسال به تلگرام"""
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
• تعداد معاملات: {r['total_trades']}
• نرخ برد: {r['win_rate']}%
• ضرر حداکثر: {r['drawdown']}%
"""

    if r['total_trades'] == 0:
        report += "\n❌ هیچ سیگنالی تولید نشد."
        return report

    report += "\n\n📌 جزئیات معاملات:\n"
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
            f"   💰 سرمایه پس از: ${t['capital_after']:.2f}\n\n"
        )
    return report


def send_long_message(text, max_len=4096):
    """ارسال پیام‌های طولانی به تلگرام در چند بخش"""
    while len(text) > max_len:
        part = text[:max_len]
        last_nl = part.rfind('\n')
        if last_nl > 0:
            part = text[:last_nl]
            text = text[last_nl:]
        else:
            part = text[:max_len]
            text = text[max_len:]
        send_telegram_message(part)
    if text.strip():
        send_telegram_message(text)


def main():
    try:
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
        df = fetch_data(symbol, timeframe, start_date, end_date)
        if df.empty:
            error_msg = f"❌ داده‌ای برای {symbol_input} در تایم‌فریم {timeframe} یافت نشد."
            send_telegram_message(error_msg)
            return

        if len(df) < 50:
            error_msg = f"❌ داده کافی برای {symbol_input} در {timeframe} موجود نیست."
            send_telegram_message(error_msg)
            return

        # --- اجرای بک‌تست ---
        result = run_backtest(df, get_signal, initial_capital=1000.0, leverage=10)

        # --- تولید گزارش ---
        report = format_report(result, symbol_input, timeframe, start_date_str, end_date_str)

        # --- ارسال به تلگرام ---
        send_long_message(report)

        # --- پیام خلاصه ---
        summary = (
            f"✅ بک‌تست {symbol_input} | "
            f"معاملات: {result['total_trades']} | "
            f"سود: ${result['total_pnl_usd']:+.2f}"
        )
        send_telegram_message(summary)

    except Exception as e:
        error_msg = (
            f"❌ خطا در اجرای بک‌تست:\n\n"
            f"<b>نماد:</b> {os.getenv('SYMBOL', 'N/A')}\n"
            f"<b>تایم‌فریم:</b> {os.getenv('TIMEFRAME', 'N/A')}\n"
            f"<b>خطا:</b> {str(e)}\n\n"
            f"<pre>{traceback.format_exc()}</pre>"
        )
        send_telegram_message(error_msg)


# اجرای برنامه وقتی فایل مستقیماً اجرا شود
if __name__ == "__main__":
    main()
