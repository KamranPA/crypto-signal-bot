# src/utils/telegram_notifier.py
import requests
import os
from datetime import datetime

def send_telegram_report(report):
    """
    ارسال گزارش بک‌تست به ربات تلگرام
    """
    # دریافت توکن و آیدی از محیط (GitHub Secrets)
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("⚠️ هشدار: TELEGRAM_BOT_TOKEN یا TELEGRAM_CHAT_ID تنظیم نشده است.")
        return

    # آخرین معامله
    last_trade = report['trades'][-1] if report['trades'] else None

    # زمان فعلی
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # اطلاعات عمومی
    symbol = os.getenv("SYMBOL", "BTC/USDT")
    timeframe = os.getenv("TIMEFRAME", "1h")
    days = os.getenv("DAYS", "30")

    # پیام اصلی
    message = f"""
🚀 *سیگنال جدید سیستم معاملاتی*

📅 زمان: {now}
📊 نماد: {symbol}
⏰ تایم فریم: {timeframe}
🗓 بازه زمانی: {days} روز

📈 *آمار معاملات*:
• تعداد کل معاملات: {report['total_trades']}
• معاملات سودده: {report['winning_trades']}
• معاملات ضررده: {report['losing_trades']}
• نرخ موفقیت: {report['win_rate']}%
• حداکثر Drawdown: ${report['drawdown']:.2f}
    """

    # اضافه کردن جزئیات آخرین معامله (اگر وجود داشته باشد)
    if last_trade:
        entry = last_trade.get('entry', 'N/A')
        sl = last_trade.get('sl', 'N/A')
        tp = last_trade.get('tp', 'N/A')

        message += f"""

🎯 *آخرین معامله*:
• نوع: {last_trade['type'].upper()}
• نقطه ورود: {entry:.2f}"""

        if sl != 'N/A':
            message += f"\n• حد ضرر: {sl:.2f}"
        else:
            message += "\n• حد ضرر: نامشخص"

        if tp != 'N/A':
            message += f"\n• حد سود: {tp:.2f}"
        else:
            message += "\n• حد سود: نامشخص"

        exit_type = last_trade.get('exit_type', 'N/A')
        message += f"\n• خروج: {exit_type}"

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
            print("✅ گزارش با موفقیت به تلگرام ارسال شد.")
        else:
            print(f"❌ خطای تلگرام: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ خطا در ارسال تلگرام: {e}")
