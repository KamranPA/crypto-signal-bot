# src/backtest/backtester.py
import pandas as pd

def run_backtest(df, strategy_func):
    trades = []
    position = None

    # اضافه کردن SMA برای استراتژی
    df['sma_20'] = df['close'].rolling(20).mean()

    for i in range(50, len(df)):
        window = df.iloc[:i+1]
        result = strategy_func(window)

        if result['signal'] == 'BUY' and not position:
            position = {
                'type': 'long',
                'entry': result['entry'],
                'sl': result['stop_loss'],
                'tp': result['take_profit'],
                'start_time': window.index[-1]
            }

        elif result['signal'] == 'SELL' and not position:
            position = {
                'type': 'short',
                'entry': result['entry'],
                'sl': result['stop_loss'],
                'tp': result['take_profit'],
                'start_time': window.index[-1]
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

            if exit_price:
                pnl = (exit_price / position['entry'] - 1) if position['type'] == 'long' \
                    else (1 - exit_price / position['entry'])
                trades.append({
                    'type': position['type'],
                    'entry': position['entry'],
                    'exit': exit_price,
                    'exit_type': exit_type,
                    'start': position['start_time'],
                    'end': current.name,
                    'pnl': pnl
                })
                position = None

    # محاسبه آمار
    total = len(trades)
    wins = len([t for t in trades if t['pnl'] > 0])
    win_rate = round(wins / total * 100, 2) if total > 0 else 0
    drawdown = (df['close'].cummax() - df['close']).max()

    return {
        'total_trades': total,
        'winning_trades': wins,
        'losing_trades': total - wins,
        'win_rate': win_rate,
        'drawdown': round(drawdown, 2),
        'trades': trades
    }
