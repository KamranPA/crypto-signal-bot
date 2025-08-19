import requests
import pandas as pd

def send_telegram_report(results, token, chat_id):
    message = f"""
📈 **گزارش بک‌تست هوشمند**
⏰ زمان: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
{'─' * 30}
"""
    for res in results:
        signal_emoji = "🟢" if res['last_signal'] == 1 else "🔴" if res['last_signal'] == -1 else "⚪"
        message += f"""
🪙 {res['symbol'].replace('-','/')}: {signal_emoji}
✅ نرخ برد: {res['win_rate']:.1%}
📊 بازده کلی: {res['total_return']:.1%}
⚡ شارپ: {res['sharpe']:.2f}
📉 ماکس دردوان: {res['max_drawdown']:.1%}
🎯 میانگین سود: {res['avg_win']:.2%}
⛔ میانگین ضرر: {res['avg_loss']:.2%}
⚖️ نسبت سود/ضرر: {res['reward_risk_ratio']:.2f}
📊 معاملات معتبر: {res['total_trades']} (موفق: {res['positive_trades']})
"""
    message += "\n#بک_تست #کیفیت_سیگنال"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}

    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            print("✅ پیام با موفقیت ارسال شد!")
        else:
            print(f"❌ خطا: {response.status_code}")
    except Exception as e:
        print(f"❌ خطا در ارتباط با تلگرام: {e}")
