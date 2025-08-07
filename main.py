# main.py
import ccxt
import pandas as pd
import time
import json
import os
from datetime import datetime, timezone
from strategy import check_signal
from telegram_bot import send_telegram_message
from utils import load_signals, save_signals, is_new_candle_closed

# تنظیمات
SYMBOL = "BTC/USDT"
TIMEFRAME = "15m"
LIMIT = 200  # تعداد کندل
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "123456789")  # جایگزین کنید
SIGNALS_FILE = "signals.json"

# بارگذاری وضعیت سیگنال‌ها
signals_db = load_signals(SIGNALS_FILE)

def main():
    # دریافت داده
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=LIMIT)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # تبدیل زمان به UTC
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    
    # بررسی بسته شدن کندل
    last_candle_time = df['datetime'].iloc[-1]
    if not is_new_candle_closed(last_candle_time):
        # فقط هر 15 دقیقه یک بار چک می‌کند
        if datetime.now(timezone.utc).minute % 60 == 0:
            send_telegram_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, "✅ سیستم فعال است")
        return

    # بررسی سیگنال
    signal = check_signal(df)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if signal:
        entry = signal['entry']
        sl = signal['stop_loss']
        tp1, tp2 = signal['take_profit']
        rr1, rr2 = signal['risk_reward']

        message = f"""
🚀 <b>سیگنال جدید BTC/USDT (15 دقیقه)</b>
📅 {now}
🎯 ورود: <b>{entry}</b>
⛔ حد ضرر: {sl}
✅ حد سود 1: {tp1} (RR: {rr1})
✅ حد سود 2: {tp2} (RR: {rr2})
📌 دلیل: {signal['reason']}
        """
        send_telegram_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, message)

        # ذخیره سیگنال
        signal_id = f"BTC_{now.replace(' ', '_').replace(':', '')}"
        signals_db[signal_id] = {
            "type": "BUY",
            "entry": entry,
            "stop_loss": sl,
            "take_profit": [tp1, tp2],
            "status": "open",
            "entry_time": now,
            "tp1_hit": False,
            "tp2_hit": False,
            "sl_hit": False
        }
        save_signals(SIGNALS_FILE, signals_db)

    # چک کردن رسیدن به TP/SL برای سیگنال‌های باز
    current_price = df['close'].iloc[-1]
    updated = False
    for sid, s in signals_db.items():
        if s['status'] == 'open':
            if current_price >= s['take_profit'][1]:
                s['status'] = 'tp2_hit'
                s['tp1_hit'] = True
                s['tp2_hit'] = True
                updated = True
            elif current_price >= s['take_profit'][0] and not s['tp1_hit']:
                s['tp1_hit'] = True
                updated = True
            elif current_price <= s['stop_loss']:
                s['status'] = 'sl_hit'
                s['sl_hit'] = True
                updated = True
    if updated:
        save_signals(SIGNALS_FILE, signals_db)

    # گزارش روزانه در نیمه‌شب UTC
    if datetime.now(timezone.utc).hour == 0 and datetime.now(timezone.utc).minute < 15:
        total = len([s for s in signals_db.values() if 'entry_time' in s])
        tp_hit = len([s for s in signals_db.values() if s.get('tp1_hit')])
        sl_hit = len([s for s in signals_db.values() if s.get('sl_hit')])
        active = len([s for s in signals_db.values() if s['status'] == 'open'])

        daily_report = f"""
📊 <b>گزارش روزانه سیگنال‌ها</b>
📆 {datetime.now(timezone.utc).strftime("%Y-%m-%d")}
🔹 تعداد کل سیگنال‌ها: {total}
🟢 رسیدن به حد سود: {tp_hit}
🔴 رسیدن به حد ضرر: {sl_hit}
🟡 در حال اجرا: {active}
⏱ آخرین بررسی: {now}
        """
        send_telegram_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, daily_report)

if __name__ == "__main__":
    main()
