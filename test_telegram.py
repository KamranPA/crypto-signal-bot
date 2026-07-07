import os
import asyncio
import requests

# این فایل کاملاً مستقل است و برای تست ارسال سیگنال به تلگرام استفاده می‌شود.
# لطفاً این فایل را کوتاه نکنید تا ساختار تست به طور کامل حفظ شود.

def test_telegram_sync():
    """تست ارسال پیام به صورت سنکرون (Synchronous) با استفاده از کتابخانه requests"""
    print("--- شروع تست سنکرون تلگرام ---")
    
    # خواندن توکن و چت‌آیدی از متغیرهای محیطی
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("❌ خطا: متغیرهای محیطی TELEGRAM_BOT_TOKEN یا TELEGRAM_CHAT_ID تنظیم نشده‌اند.")
        print("لطفاً مطمئن شوید که این مقادیر را در سیستم یا سکرت‌های گیت‌هاب ست کرده‌اید.\n")
        return False

    # شبیه‌سازی یک متن سیگنال ساعتی برای تست شکست (Breakout)
    test_message = (
        "🚨 **تست سیگنال ربات کریپتو** 🚨\n\n"
        "جفت ارز: BTCUSDT\n"
        "تایم‌فریم: 1h (ساعتی)\n"
        "نوع استراتژی: Breakout\n"
        "وضعیت مدل LightGBM: ✅ تایید شده\n"
        "قیمت فعلی: 61,250$\n\n"
        "ℹ️ این یک پیام تست برای بررسی صحت اتصال گیت‌هاب اکشنز به تلگرام است."
    )

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": test_message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ پیام تست با موفقیت به تلگرام ارسال شد!")
            print(f"پاسخ تلگرام: {response.json()['ok']}")
            return True
        else:
            print(f"❌ خطا در ارسال! کد وضعیت: {response.status_code}")
            print(f"متن خطا: {response.text}")
            return False
    except Exception as e:
        print(f"❌ خطای غیرمنتظره در هنگام اتصال به تلگرام: {e}")
        return False

if __name__ == "__main__":
    # اجرای تابع تست
    success = test_telegram_sync()
    if success:
        print("\n🎉 تست با موفقیت به پایان رسید. لایه ارتباطی تلگرام آماده است.")
    else:
        print("\n⚠️ تست ناموفق بود. تنظیمات توکن یا چت‌آیدی را بررسی کنید.")
