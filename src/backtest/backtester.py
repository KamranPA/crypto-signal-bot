# src/backtest/backtester.py

import pandas as pd

def run_backtest(df, strategy_func, initial_capital=1000.0, leverage=10):
    """
    اجرای بک‌تست روی داده‌ها با یک استراتژی
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
        strategy_name = signal_result.get('strategy', 'Unknown')  # ✅

        # فیلتر مقادیر
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
                'regime': regime,
                'strategy': strategy_name
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
                'regime': regime,
                'strategy': strategy_name
            }

        # بررسی خروج
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
                # محاسبه سود/ضرر نسبت به قیمت
                if position['type'] == 'long':
                    price_change_pct = (exit_price - position['entry']) / position['entry']
                else:
                    price_change_pct = (position['entry'] - exit_price) / position['entry']

                pnl_usd = position['position_size'] * price_change_pct
                current_capital += pnl_usd

                # ذخیره معامله
                trade = {
                    'type': position['type'],
                    'entry': position['entry'],
                    'exit': exit_price,
                    'exit_type': exit_type,
                    'start': position['start_time'],
                    'end': current.name,
                    'duration_h': round((current.name - position['start_time']).total_seconds() / 3600, 2),
                    'pnl_percent': round(price_change_pct * 100, 2),
                    'pnl_usd': round(pnl_usd, 2),
                    'capital_after': round(current_capital, 2),
                    'sl': position['sl'],
                    'tp': position['tp'],
                    'regime': position['regime'],
                    'strategy': position['strategy']
                }
                trades.append(trade)
                position = None

    # محاسبه معیارهای عملکرد
    total_pnl_usd = sum(t['pnl_usd'] for t in trades)
    total_trades = len(trades)
    winning_trades = len([t for t in trades if t['pnl_usd'] > 0])
    win_rate = round(winning_trades / total_trades * 100, 2) if total_trades > 0 else 0

    # محاسبه ضرر حداکثر (Max Drawdown)
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
        'total_pnl_usd': round(total_pnl_usd, 2),
        'final_capital': round(current_capital, 2),
        'trades': trades
    }
