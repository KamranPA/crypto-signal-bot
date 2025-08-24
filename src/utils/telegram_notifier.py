# src/utils/telegram_notifier.py
import requests
import os
from datetime import datetime

def send_telegram_report(report):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    print("🔍 --- دیباگ ارسال تلگرام ---")
    print(f"Token موجود: {'بله' if token else 'خیر'}")
    print(f"Chat ID موجود: {'بله' if chat_id else 'خیر'}")

    if not token or not chat_id:
        print("❌ ارسال لغو شد: TOKEN یا CHAT_ID تنظیم نشده")
        return

    try:
        chat_id_int = int(chat_id)
        print(f"✅ Chat ID معتبر: {chat_id_int}")
    except:
        print(f"❌ Chat ID نامعتبر: {chat_id}")
        return

    # ساخت پیام بدون ایموجی‌های غیرضروری
    symbol = os.getenv("SYMBOL", "BTC/USDT")
    timeframe = os.getenv("TIMEFRAME", "1h")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    message = f"""
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

    if report['trades']:
        message += "\n📋 *جزئیات معاملات*:\n"
        for i, trade in enumerate(report['trades'],1):
            entry = trade['entry']
            sl = trade['sl']
            tp = trade['tp']
            start = trade['start'].strftime("%Y-%m-%d %H:%M")
            pnl_usd = trade['pnl_usd']
            emoji = "🟢" if pnl_usd > 0 else "🔴"

            message += f"""
{i}. { emoji} {trade['type'].upper()} ({trade['regime']})
   📅 {start}
   💵 ورود: {entry:.2f}
   ⚠️ حد ضرر: {sl:.2f}
   🎯 حد سود: {tp:.2f}
   💹 سود/زیان: ${pnl_usd:,.2f}
   🔚 خروج: {trade['exit_type']}
"""
    else:
        message += "\n📋 *هیچ معامله‌ای انجام نشد.*"

    print(f"📤 در حال ارسال پیام به تلگرام... طول پیام: {len(message)} کاراکتر")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    try:
        response = requests.post(url, data=payload, timeout=15)
        print(f"📡 وضعیت پاسخ تلگرام: {response.status_code}")
        print(f"📦 پاسخ: {response.text}")

        if response.status_code == 200:
            print("✅ پیام با موفقیت ارسال شد!")
        else:
            print("❌ خطا در ارسال پیام.")
    except Exception as e:
        # ✅ اصلاح: استفاده از str() برای ایموجی‌ها
        print("❌ خطا در ارسال: " + str(e))
