# src/utils/telegram_notifier.py
import requests
import os
from datetime import datetime

def send_telegram_message(token, chat_id, text, parse_mode=None):
    """
    ارسال پیام به تلگرام با قابلیت غیرفعال کردن parse_mode
    """
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        response = requests.post(url, data=payload, timeout=15)
        if response.status_code == 200:
            return True
        else:
            print(f"❌ خطا در ارسال پیام: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"🚫 خطا در ارسال: {e}")
        return False

def split_message(message, max_length=3500):
    """
    تقسیم پیام در آخرین خط جدید قبل از محدودیت
    """
    parts = []
    while len(message) > max_length:
        # پیدا کردن آخرین خط جدید قبل از محدودیت
        split_index = message.rfind('\n', 0, max_length)
        if split_index == -1:  # اگر خط جدید نبود
            split_index = max_length
        parts.append(message[:split_index])
        message = message[split_index:].lstrip()  # حذف فاصله اول
    parts.append(message)
    return parts

def send_telegram_report(report):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("❌ ارسال لغو شد: TELEGRAM_BOT_TOKEN یا CHAT_ID تنظیم نشده")
        return

    try:
        int(chat_id)
    except:
        print(f"❌ Chat ID نامعتبر: {chat_id}")
        return

    symbol = os.getenv("SYMBOL", "BTC/USDT")
    timeframe = os.getenv("TIMEFRAME", "1h")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 🔹 1. ارسال خلاصه با Markdown (فرمت خوب)
    summary = f"""
🚀 *سیگنال جدید سیستم معاملاتی*

📅 زمان: {now}
📊 نماد: {symbol}
⏰ تایم فریم: {timeframe}
🗓 بازه: {report.get('start_date', 'N/A')} تا {report.get('end_date', 'N/A')}

🏦 *مدیریت سرمایه (1000$ + لوریج 10x)*
• سرمایه اولیه: $1000
• سرمایه نهایی: ${report['final_capital']:,.2f}
• سود/زیان کل: ${report['total_pnl_usd']:,.2f} {'(سود)' if report['total_pnl_usd'] > 0 else '(ضرر)'}

📈 *آمار کلی*:
• تعداد معاملات: {report['total_trades']}
• سودده: {report['winning_trades']}
• ضررده: {report['losing_trades']}
• نرخ موفقیت: {report['win_rate']}%
• Drawdown: {report['drawdown']}%
"""

    if not send_telegram_message(token, chat_id, summary.strip(), parse_mode="Markdown"):
        print("❌ ارسال خلاصه ناموفق بود.")
        return

    # 🔹 2. ارسال جزئیات معاملات بدون Markdown (فقط متن ساده)
    if report['trades']:
        details = "📋 جزئیات معاملات:\n"
        for i, trade in enumerate(report['trades'], 1):
            entry = trade['entry']
            sl = trade['sl']
            tp = trade['tp']
            start = trade['start'].strftime("%Y-%m-%d %H:%M")
            pnl_usd = trade['pnl_usd']
            result = "سود" if pnl_usd > 0 else "ضرر"

            details += f"""
{i}. {trade['type'].upper()} | {trade['regime']}
   تاریخ: {start}
   ورود: {entry:.2f}
   حد ضرر: {sl:.2f}
   حد سود: {tp:.2f}
   خروج: {trade['exit_type']} 
   سود/زیان: ${pnl_usd:,.2f} ({result})
---
"""
        # تقسیم جزئیات به بخش‌های کوچک
        detail_parts = split_message(details, 3500)
        for part in detail_parts:
            if not send_telegram_message(token, chat_id, part.strip()):
                print("⚠️ یک بخش جزئیات ارسال نشد.")
            else:
                print("📤 بخشی از جزئیات معاملات ارسال شد.")
    else:
        send_telegram_message(token, chat_id, "📋 هیچ معامله‌ای انجام نشد.")

    print("✅ گزارش کامل با موفقیت ارسال شد.")
