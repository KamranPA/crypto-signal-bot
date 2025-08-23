# src/utils/telegram_notifier.py (نسخه اصلاح‌شده)
import requests
import os
from datetime import datetime

def send_telegram_report(report):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("⚠️ هشدار: TELEGRAM_BOT_TOKEN یا CHAT_ID تنظیم نشده است.")
        return

    last_trade = report['trades'][-1] if report['trades'] else None

    # اطلاعات عمومی
    symbol = os.getenv("SYMBOL", "BTC/USDT")
    timeframe = os.getenv("TIMEFRAME", "1h")
    days = os.getenv("DAYS", "30")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # پیام با فرمت حرفه‌ای
    message = f"""
🚀 *سیگنال جدید سیستم معاملاتی* 🚀

📅 زمان: {now}
📊 نماد: {symbol}
⏰ تایم فریم: {timeframe}
🗓 بازه زمانی: {days} روز

📈 *آمار معاملاتی*:
• تعداد کل معاملات: {report['total_trades']}
• معاملات سودده: {report['winning_trades']} ✅
• معاملات ضررده: {report['losing_trades']} ❌
• نرخ موفقیت: {report['win_rate']}% 💯
• Drawdown: {report['drawdown']}% 📉

🎯 *آخرین معامله*:
• نوع: {last_trade['type'].upper()} 📈
• نقطه ورود: {last_trade['entry']:.2f} 💵
• حد ضرر (SL): {last_trade.get('sl', 'N/A'):.2f} ⚠️
• حد سود (TP): {last_trade.get('tp', 'N/A'):.2f} 🎯
• خروج: {last_trade['exit_type']} 🔚
"""

    # ارسال به تلگرام
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            print("✅ گزارش با موفقیت ارسال شد.")
        else:
            print(f"❌ خطای تلگرام: {response.status_code}")
    except Exception as e:
        print(f"❌ خطا در ارسال: {e}")
