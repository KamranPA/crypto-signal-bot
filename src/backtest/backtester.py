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
                if current['high
