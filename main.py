# main.py
import ccxt
import pandas as pd
from datetime import datetime
import argparse

from utils.data_loader import fetch_ohlcv
from strategy.technical import add_indicators
from strategy.fusion import generate_signal
from risk.money_management import calculate_sl_tp
from backtest.engine import run_backtest
from backtest.report import print_summary

def main():
    print("🚀 سیستم بک‌تست معاملاتی دوطرفه (Long/Short) - ارزهای دیجیتال")
    print("-" * 60)

    # ورودی کاربر
    symbol = input("🔸 نماد (مثلاً BTC/USDT): ").strip().upper()
    timeframe = input("⏰ تایم‌فریم (مثلاً 15m): ").strip()
    since = input("📅 تاریخ شروع (مثلاً 2024-01-01): ").strip()
    risk_reward_ratio = float(input("🎯 نسبت ریسک به ریوارد (حداقل 2): ") or "2")

    # تنظیم حداقل 2:1
    if risk_reward_ratio < 2:
        print("⚠️  نسبت ریسک به ریوارد باید حداقل 2 باشد. مقدار 2 تنظیم شد.")
        risk_reward_ratio = 2

    print(f"\n📥 در حال دریافت داده‌ها برای {symbol} در تایم‌فریم {timeframe} از {since}...")
    
    try:
        # دریافت داده
        df = fetch_ohlcv(symbol, timeframe, since)
        df = add_indicators(df)
        
        # تولید سیگنال
        signals = []
        for i in range(len(df) - 1):
            row = df.iloc[i]
            next_close = df.iloc[i + 1]['close']
            signal = generate_signal(row)
            if signal != 0:
                sl, tp = calculate_sl_tp(row['close'], row['atr'], signal, risk_reward_ratio)
                result = {
                    'timestamp': row['timestamp'],
                    'price': row['close'],
                    'signal': 'Long' if signal == 1 else 'Short',
                    'sl': sl,
                    'tp': tp,
                    'reached': None
                }
                # بررسی آیا حد سود/ضرر در کندل بعدی لمس شده
                high, low = next_close, next_close
                if i + 2 < len(df):
                    high = df.iloc[i + 1:i + 3]['high'].max()
                    low = df.iloc[i + 1:i + 3]['low'].min()

                if signal == 1:  # Long
                    if low <= sl:
                        result['reached'] = 'SL'
                    elif high >= tp:
                        result['reached'] = 'TP'
                elif signal == -1:  # Short
                    if high >= sl:
                        result['reached'] = 'SL'
                    elif low <= tp:
                        result['reached'] = 'TP'

                signals.append(result)

        # گزارش
        print_summary(signals)

    except Exception as e:
        print(f"❌ خطای سیستم: {e}")

if __name__ == "__main__":
    main()
