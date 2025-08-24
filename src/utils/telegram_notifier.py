# src/utils/telegram_notifier.py
import requests
import os
from datetime import datetime

def send_telegram_message(token, chat_id, text):
    """ارسال یک پیام کوتاه به تلگرام"""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, data=payload, timeout=15)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ خطای شبکه: {e}")
        return False

def split_message(message, max_length=4000):
    """تقسیم پیام به بخش‌های کوتاه‌تر"""
    parts = []
    while len(message) > max_length:
        split_index = message.rfind('\n', 0, max_length)
        if split_index == -1:
            split_index = max_length
        parts.append(message[:split_index])
        message = message[split_index:]
    parts.append(message)
    return parts

def send_telegram_report(report):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("❌ ارسال لغو شد: TELEGRAM_BOT_TOKEN یا CHAT_ID تنظیم نشده")
        return

    try:
        chat_id_int = int(chat_id)
    except:
        print(f"❌ Chat ID نامعتبر: {chat_id}")
        return

    # ساخت پیام اصلی (بدون جزئیات معاملات)
    symbol = os.getenv("SYMBOL", "BTC/USDT")
    timeframe = os.getenv("TIMEFRAME", "1h")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    summary = f"""
🚀 *سیگنال جدید سیستم معاملاتی* 

📅 زمان: {now}
📊 نماد: {symbol}
⏰ تایم فریم: {timeframe}
🗓 بازه: {report.get('start_date', 'N/A')} تا {report.get('end_date', 'N/A')}

🏦 *مدیریت سرمایه (1000$ + لوریج 10x)*
• سرمایه اولیه: $1000
• سرمایه نهایی: ${report['final_capital']:,.2f}
• سود/زیان کل: ${report['total_pnl_usd']:,.2f} {'🟢' if report['total_pnl_usd'] > 0 else '🔴'}

📈 *آمار کلی*:
• تعداد معاملات: {report['total_trades']}
• سودده: {report['winning_trades']} ✅
• ضررده: {report['losing_trades']} ❌
• نرخ موفقیت: {report['win_rate']}% 💯
• Drawdown: {report['drawdown']}% 📉
"""

    # ارسال خلاصه
    if not send_telegram_message(token, chat_id, summary):
        print("❌ ارسال خلاصه ناموفق بود.")
        return

    # ارسال جزئیات معاملات به صورت تکی یا گروهی
    if report['trades']:
        details = "\n📋 *جزئیات معاملات*:\n"
        for i, trade in enumerate(report['trades'], 1):
            entry = trade['entry']
            sl = trade['sl']
            tp = trade['tp']
            start = trade['start'].strftime("%Y-%m-%d %H:%M")
            pnl_usd = trade['pnl_usd']
            emoji = "🟢" if pnl_usd > 0 else "🔴"

            trade_msg = f"""
{i}. {emoji} {trade['type'].upper()} ({trade['regime']})
   📅 {start}
   💵 ورود: {entry:.2f}
   ⚠️ حد ضرر: {sl:.2f}
   🎯 حد سود: {tp:.2f}
   💹 سود/زیان: ${pnl_usd:,.2f}
   🔚 خروج: {trade['exit_type']}
"""
            details += trade_msg

        # تقسیم جزئیات به بخش‌های کوتاه‌تر
        detail_parts = split_message(details, 3500)  # حاشیه امنیت
        for part in detail_parts:
            if not send_telegram_message(token, chat_id, part):
                print("⚠️ یک بخش جزئیات ارسال نشد.")
            else:
                print("📤 بخشی از جزئیات ارسال شد.")
    else:
        send_telegram_message(token, chat_id, "📋 هیچ معامله‌ای انجام نشد.")

    print("✅ گزارش با موفقیت ارسال شد.")
