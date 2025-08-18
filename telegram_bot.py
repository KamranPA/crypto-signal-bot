import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, SEND_TELEGRAM

def send_telegram_report(report):
    if not SEND_TELEGRAM:
        return
    message = f"""
📈 **گزارش بک‌تست هوشمند**
⏰ زمان: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
{'─' * 30}
"""
    for res in report:
        signal_emoji = "🟢" if res['last_signal'] == 1 else "🔴" if res['last_signal'] == -1 else "⚪"
        message += f"""
🪙 {res['symbol'].replace('-','/')}: {signal_emoji}
✅ نرخ برد: {res['win_rate']:.1%}
⚡ شارپ: {res['sharpe']:.2f}
📉 ماکس دردوان: {res['max_drawdown']:.1%}
📊 معاملات: {res['total_trades']} (موفق: {res['positive_trades']})
"""
    message += "\n#بک_تست #هوش_مصنوعی"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})
