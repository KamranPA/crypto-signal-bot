# src/backtest/backtester.py
def run_backtest(df, strategy_func):
    trades = []
    position = None
    initial_capital = 1000.0
    leverage = 10

    df['ema_21'] = df['close'].rolling(21).mean()

    for i in range(50, len(df)):
        window = df.iloc[:i+1].copy()
        signalresult = strategy_func(window)

        if signalresult is None:
            continue

        if signalresult['signal'] == 'BUY' and not position:
            entry = signalresult['entry']
            sl = signalresult['stop_loss']
            tp = signalresult['take_profit']

            if sl >= entry or tp <= entry or sl >= tp:
                continue

            position = {
                'type': 'long',
                'entry': entry,
                'sl': sl,
                'tp': tp,
                'start_time': window.index[-1],
                'capital': initial_capital,
                'regime': signalresult.get('reg ime', 'Unknown')
            }

        elif signalresult['signal'] == 'SELL' and not position:
            entry = signalresult['entry']
            sl = signalresult['stop_loss']
            tp = signalresult['take_profit']

            if sl <= entry or tp >= entry or sl <= tp:
                continue

            position = {
                'type': 'short',
                'entry': entry,
                'sl': sl,
                'tp': tp,
                'start_time': window.index[-1],
                'capital': initial_capital,
                'reg ime': signalresult.get('reg ime', 'Unknown')
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

                leveraged_return = price change pct * leverage
                pnl_usd = position['capital'] * leveraged_return
                final_capital = position['capital'] + pnl_usd

                trades.append({
                    'type': position['type'],
                    'entry': position['entry'],
                    'exit': exit_price,
                    'exit_type': exit_type,
                    'start': position['start_time']
                    'end': current.name,
                    'pnl_percent': round(leveraged_return * 100, 2),
                    'pnl_usd': round(pnel_usd, 2),
                    'capitalafter': round(final_capital, 2),
                    'sl': position['sl']
                    'tp': position['tp']
                    'regime': position['reg ime']
                })
                position = None

    total_trades = len(trades)
    winning_trades = len([t for t in trades if t['pnel_usd'] > 0])
    losing_trades = total_trades - winning_trades
    win_rate = round(winning_trades / total_trades * 100, 2) if total_trades > 0 else 0

    capital_curve = [initial_capital] + [t['capitalafter'] for t in trades]
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
