# src/backtest/backtester.py
import pandas as pd

def run_backtest(df, strategy_func):
    """
    اجرای بک‌تست و محاسبه آمار معاملاتی
    """
    trades = []
    position = None

    # محاسبه SMA برای استراتژی
    df['sma_20'] = df['close'].rolling(20).mean()

    for i in range(50, len(df)):
        window = df.iloc[:i+1]
        signal_result = strategy_func(window)

        # ورود به معامله
        if signal_result['signal'] == 'BUY' and not position:
            position = {
                'type': 'long',
                'entry': signal_result['entry'],
                'sl': signal_result['stop_loss'],
                'tp': signal_result['take_profit'],
                'start_time': window.index[-1]
            }

        elif signal_result['signal'] == 'SELL' and not position:
            position = {
                'type': 'short',
                'entry': signal_result['entry'],
                'sl': signal_result['stop_loss'],
                'tp': signal_result['take_profit'],
                'start_time': window.index[-1]
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
                pnl = (exit_price / position['entry'] - 1) if position['type'] == 'long' \
                    else (1 - exit_price / position['entry'])

                trades.append({
                    'type': position['type'],
                    'entry': position['entry'],
                    'exit': exit_price,
                    'exit_type': exit_type,
                    'start': position['start_time'],
                    'end': current.name,
                    'pnl': pnl,
                    'sl': position['sl'],
                    'tp': position['tp']
                })
                position = None

    # محاسبه آمار
    total_trades = len(trades)
    winning_trades = len([t for t in trades if t['pnl'] > 0])
    losing_trades = total_trades - winning_trades
    win_rate = round(winning_trades / total_trades * 100, 2) if total_trades > 0 else 0

    # 🔁 محاسبه Drawdown به صورت درصدی
    peak = df['close'].cummax()
    drawdown_pct = ((peak - df['close']) / peak) * 100
    max_drawdown = drawdown_pct.max()

    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': win_rate,
        'drawdown': round(max_drawdown, 2),  # حالا درصد است
        'trades': trades
    }
