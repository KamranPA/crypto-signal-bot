# src/utils/telegram_notifier.py
import requests
import os
from datetime import datetime

def send_telegram_report(report):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("⚠️ هشدار: TELEGRAM_BOT_TOKEN یا CHAT_ID تنظیم نشده است.")
        return

    symbol = os.getenv("SYMBOL", "BTC/USDT")
    timeframe = os.getenv("TIMEFRAME", "1h")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # پیام اصلی
    message = f"""
🚀 *سیگنال جدید سیستم معاملاتی* 🚀

📅 زمان اجرا: {now}
📊 نماد: {symbol}
⏰ تایم فریم: {timeframe}
🗓 بازه: {report.get('start_date', 'N/A')} تا {report.get('end_date', 'N/A')}

📈 *آمار کلی*:
• تعداد معاملات: {report['total_trades']}
• سودده: {report['winning_trades']} ✅
• ضررده: {report['losing_trades']} ❌
• نرخ موفقیت: {report['win_rate']}% 💯
• Drawdown: {report['drawdown']}% 📉
"""

    # اضافه کردن جزئیات معاملات
    if report['trades']:
        message += "\n📋 *جزئیات معاملات*:\n"
        for i, trade in enumerate(report['trades'], 1):
            entry = trade.get('entry', 'N/A')
            sl = trade.get('sl', 'N/A')
            tp = trade.get('tp', 'N/A')
            start = trade['start'].strftime("%Y-%m-%d %H:%M")
            exit_type = trade['exit_type']
            pnl_sign = "🟢" if trade['pnl'] > 0 else "🔴"

            message += f"""
{i}. {pnl_sign} {trade['type'].upper()}
   📅 {start}
   💵 ورود: {entry:.2f}
   ⚠️ حد ضرر: {sl:.2f}
   🎯 حد سود: {tp:.2f}
   🔚 خروج: {exit_type}
"""
    else:
        message += "\n📋 *هیچ معامله‌ای انجام نشد.*"

    # ارسال به تلگرام
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            print("✅ گزارش با موفقیت ارسال شد.")
        else:
            print(f"❌ خطای تلگرام: {response.status_code}")
    except Exception as e:
        print(f"❌ خطا در ارسال: {e}")
