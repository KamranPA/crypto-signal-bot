# src/utils/telegram_notifier.py
import requests
import os
from datetime import datetime

def send_telegram_report(report):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("⚠️ TELEGRAM_BOT_TOKEN یا CHAT_ID تنظیم نشده است.")
        return

    last_trade = report['trades'][-1] if report['trades'] else None

    message = f"""
🚀 *سیگنال جدید سیستم معاملاتی*

📅 زمان: {datetime.now().strftime("%Y-%m-%d %H:%M")}
📊 نماد: {os.getenv('SYMBOL', 'BTC/USDT')}
⏰ تایم فریم: {os.getenv('TIMEFRAME', '1h')}
🗓 بازه: {os.getenv('DAYS', '30')} روز

📈 آمار معاملات:
• تعداد کل: {report['total_trades']}
• حد سود: {report['winning_trades']}
• حد ضرر: {report['losing_trades']}
• نرخ موفقیت: {report['win_rate']}%
• Drawdown: ${report['drawdown']:.2f}
"""

    if last_trade:
        message += f"""

🎯 آخرین معامله:
• نوع: {last_trade['type'].upper()}
• ورود: {last_trade['entry']:.2f}
• حد سود: {last_trade['tp']:.2f}
• حد ضرر: {last_trade['sl']:.2f}
• خروج: {last_trade['exit_type']}
"""

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"❌ ارسال تلگرام ناموفق: {e}")
