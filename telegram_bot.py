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
⚡ شارپ: {res['sharpe']:.2f}
📉 ماکس دردوان: {res['max_drawdown']:.1%}
📊 معاملات: {res['total_trades']} (موفق: {res['positive_trades']})
"""
    message += "\n#بک_تست #هوش_مصنوعی"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}

    print(f"📤 در حال ارسال به تلگرام...")
    print(f"🔗 URL: {url}")
    print(f"📩 پیام: {message[:150]}...")

    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            print("✅ پیام با موفقیت ارسال شد!")
        else:
            print(f"❌ خطا: {response.status_code}")
            print(f"📝 پاسخ: {response.text}")
    except Exception as e:
        print(f"❌ خطا در ارتباط با تلگرام: {e}")
