# src/backtest/backtester.py
import pandas as pd

def run_backtest(df, strategy_func):
    trades = []
    position = None

    for i in range(50, len(df)):  # شروع بعد از محاسبه شاخص‌ها
        window = df.iloc[:i+1]
        result = strategy_func(window.copy())

        if result['signal'] == 'BUY' and not position:
            entry = result['entry']
            sl = result['stop_loss']
            tp = result['take_profit']
            position = {
                'type': 'long',
                'entry': entry,
                'sl': sl,
                'tp': tp,
                'start_time': window.index[-1]
            }

        elif result['signal'] == 'SELL' and not position:
            entry = result['entry']
            sl = result['stop_loss']
            tp = result['take_profit']
            position = {
                'type': 'short',
                'entry': entry,
                'sl': sl,
                'tp': tp,
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
                trades.append({
                    'type': position['type'],
                    'entry': position['entry'],
                    'exit': exit_price,
                    'exit_type': exit_type,
                    'start': position['start_time'],
                    'end': current.name,
                    'pnl': (exit_price / position['entry'] - 1) if position['type']=='long' else (1 - exit_price / position['entry'])
                })
                position = None

    # محاسبه آمار
    df_trades = pd.DataFrame(trades)
    total = len(df_trades)
    wins = len(df_trades[df_trades['pnl'] > 0])
    win_rate = wins / total if total > 0 else 0
    drawdown = (df['close'].cummax() - df['close']).max()

    return {
        'total_trades': total,
        'winning_trades': wins,
        'losing_trades': total - wins,
        'win_rate': round(win_rate * 100, 2),
        'drawdown': round(drawdown, 2),
        'trades': trades
    }
