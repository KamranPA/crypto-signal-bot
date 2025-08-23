# src/backtest/backtester.py
import pandas as pd

def run_backtest(df, strategy_func):
    """
    اجرای بک‌تست با شبیه‌سازی معاملات با لوریج 10x و سرمایه 1000 دلار
    فقط معاملات با SL/TP منطقی ذخیره می‌شوند
    """
    trades = []
    position = None
    initial_capital = 1000.0  # دلار
    leverage = 10

    # محاسبه EMA برای استراتژی
    df['ema_21'] = df['close'].rolling(21).mean()

    for i in range(50, len(df)):
        window = df.iloc[:i+1]
        signal_result = strategy_func(window)

        # ورود به معامله
        if signal_result['signal'] == 'BUY' and not position:
            entry = signal_result['entry']
            sl = signal_result['stop_loss']
            tp = signal_result['take_profit']

            # ✅ بررسی منطقی بودن SL و TP برای BUY
            if sl >= entry or tp <= entry or sl >= tp:
                print(f"⚠️ سیگنال BUY با SL/TP غیرمنطقی نادیده گرفته شد: entry={entry:.2f}, SL={sl:.2f}, TP={tp:.2f}")
                continue

            position = {
                'type': 'long',
                'entry': entry,
                'sl': sl,
                'tp': tp,
                'start_time': window.index[-1],
                'capital': initial_capital,
                'regime': signal_result.get('regime', 'Unknown')
            }

        elif signal_result['signal'] == 'SELL' and not position:
            entry = signal_result['entry']
            sl = signal_result['stop_loss']
            tp = signal_result['take_profit']

            # ✅ بررسی منطقی بودن SL و TP برای SELL
            if sl <= entry or tp >= entry or sl <= tp:
                print(f"⚠️ سیگنال SELL با SL/TP غیرمنطقی نادیده گرفته شد: entry={entry:.2f}, SL={sl:.2f}, TP={tp:.2f}")
                continue

            position = {
                'type': 'short',
                'entry': entry,
                'sl': sl,
                'tp': tp,
                'start_time': window.index[-1],
                'capital': initial_capital,
                'regime': signal_result.get('regime', 'Unknown')
            }

        # خروج از معامله
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
                # محاسبه بازدهی با لوریج
                if position['type'] == 'long':
                    price_change_pct = (exit_price - position['entry']) / position['entry']
                else:
                    price_change_pct = (position['entry'] - exit_price) / position['entry']

                leveraged_return = price_change_pct * leverage
                pnl_usd = position['capital'] * leveraged_return
                final_capital = position['capital'] + pnl_usd

                # ✅ فقط اگر SL/TP معتبر بود، ذخیره کن
                trades.append({
                    'type': position['type'],
                    'entry': position['entry'],
                    'exit': exit_price,
                    'exit_type': exit_type,
                    'start': position['start_time'],
                    'end': current.name,
                    'pnl_percent': round(leveraged_return * 100, 2),
                    'pnl_usd': round(pnl_usd, 2),
                    'capital_after': round(final_capital, 2),
                    'sl': position['sl'],
                    'tp': position['tp'],
                    'regime': position['regime']
                })
                position = None

    # محاسبه آمار کلی
    total_trades = len(trades)
    winning_trades = len([t for t in trades if t['pnl_usd'] > 0])
    losing_trades = total_trades - winning_trades
    win_rate = round(winning_trades / total_trades * 100, 2) if total_trades > 0 else 0

    # Drawdown بر اساس منحنی سرمایه
    capital_curve = [initial_capital] + [t['capital_after'] for t in trades]
    peak = pd.Series(capital_curve).cummax()
    drawdown_pct = ((peak - pd.Series(capital_curve)) / peak) * 100
    max_drawdown = drawdown_pct.max()

    total_pnl_usd = sum(t['pnl_usd'] for t in trades)

    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': win_rate,
        'drawdown': round(max_drawdown, 2),
        'total_pnl_usd': round(total_pnl_usd, 2),
        'final_capital': round(capital_curve[-1], 2),
        'trades': trades
    }
