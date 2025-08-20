import requests
import pandas as pd

def send_telegram_report(results, token, chat_id):
    message = f"""
📈 **گزارش بک‌تست هوشمند**
⏰ زمان: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
{'─' * 30}
"""
    for res in results:
        # ایموجی سیگنال
        signal_emoji = "🟢" if res['last_signal'] == 1 else "🔴" if res['last_signal'] == -1 else "⚪"
        
        # رنگ نسبت سود/ضرر
        rr_color = "✅" if res['reward_risk_ratio'] >= 2.0 else "⚠️" if res['reward_risk_ratio'] >= 1.0 else "❌"
        
        # رنگ بازده
        return_color = "🟢" if res['total_return'] > 0 else "🔴"

        message += f"""
🪙 {res['symbol'].replace('-','/')}: {signal_emoji}
{return_color} بازده کلی: {res['total_return']:.1%}
✅ نرخ برد: {res['win_rate']:.1%}
⚡ شارپ: {res['sharpe']:.2f}
📉 ماکس دردوان: {res['max_drawdown']:.1%}
🎯 میانگین سود: {res['avg_win']:.2%}
⛔ میانگین ضرر: {res['avg_loss']:.2%}
{rr_color} نسبت سود/ضرر: {res['reward_risk_ratio']:.2f}
📊 معاملات معتبر: {res['total_trades']} (موفق: {res['positive_trades']})
"""
    message += "\n#بک_تست #مدیریت_ریسک #کیفیت_سیگنال"

    # ارسال به تلگرام
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}

    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            print("✅ پیام با موفقیت ارسال شد!")
        else:
            print(f"❌ خطا در ارسال پیام: {response.status_code}")
    except Exception as e:
        print(f"❌ خطا در ارتباط با تلگرام: {e}")
