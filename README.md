<!-- مسیر فایل: README.md -->
# Mutanabby AI — Crypto Signal System

سیستم سیگنال‌دهی خودکار کریپتو (تایم‌فریم ۱ ساعته) بر پایه‌ی اندیکاتور `Mutanabby_AI | Fresh Algo V24`،
با بک‌تست، مدل یادگیری ماشین اختصاصی هر ارز، بهینه‌سازی خودکار پارامترها، اجرای ساعتی از طریق
GitHub Actions، ارسال سیگنال به تلگرام، و ذخیره‌سازی در Supabase.

📄 سند کامل معماری و تصمیمات طراحی: [`architecture.md`](./architecture.md)

## نصب سریع

```bash
git clone <repo-url>
cd mutanabby-signal-system
pip install -r requirements.txt
cp .env.example .env   # مقادیر را پر کنید
```

## متغیرهای محیطی (`.env`)

| متغیر | توضیح |
|---|---|
| `TELEGRAM_BOT_TOKEN` | توکن ربات تلگرام |
| `TELEGRAM_CHAT_ID` | آیدی چت مقصد سیگنال‌ها |
| `SUPABASE_URL` / `SUPABASE_KEY` | اتصال به Supabase |

در GitHub Actions این مقادیر باید به‌عنوان **Repository Secrets** ثبت شوند
(Settings → Secrets and variables → Actions).

## راه‌اندازی جداول Supabase
طرح کامل جداول در `architecture.md` بخش ۹ آمده — اسکریپت SQL را در Supabase SQL Editor اجرا کنید.

## اجرای دستی

```bash
# سیگنال ساعتی (یک‌بار، برای تست)
python -m jobs.hourly_signal

# ری‌ترین کامل + بهینه‌سازی + بک‌تست (سنگین، معمولاً ماهانه)
python -m jobs.monthly_retrain

# اجرای تست‌ها
pytest tests/ -v
```

## اجرای خودکار
دو ورک‌فلوی GitHub Actions به‌صورت پیش‌فرض فعال هستند:
- `hourly_signal.yml` — هر ساعت، ۵ دقیقه بعد از بسته‌شدن کندل
- `monthly_retrain.yml` — اول هر ماه

هر دو با `workflow_dispatch` هم قابل اجرای دستی از تب Actions گیت‌هاب هستند.

## گزارش‌های بک‌تست
بعد از هر اجرای ری‌ترین ماهانه، فایل‌های HTML تعاملی در `reports/` تولید و commit می‌شوند
(`backtest_{SYMBOL}_{تاریخ}.html`) به‌همراه یک `reports/summary.md` خلاصه برای کل واچ‌لیست.

## وضعیت فعلی پروژه
این نسخه، **اسکلت کامل و قابل‌اجرای فاز ۱** طرح است:
- ✅ ترجمه‌ی دقیق منطق اندیکاتور Pine→Python + تست صحت
- ✅ منطق مشترک سیگنال (بک‌تست/لایو یکسان)
- ✅ لایه‌ی دیتا (CoinEx + Yahoo + Calibration)
- ✅ موتور بک‌تست + گزارش‌گیری
- ✅ Pipeline کامل ML (labeling → train → predict)
- ✅ بهینه‌سازی Optuna (ریسک + آستانه ML) با Walk-Forward + Blending
- ✅ اتصال تلگرام و Supabase
- ✅ GitHub Actions (ساعتی + ماهانه)

### قبل از اجرای واقعی روی سرمایه‌ی واقعی
- [ ] تنظیم Secrets در GitHub
- [ ] اجرای اولیه‌ی `monthly_retrain` برای ساخت اولین نسخه‌ی مدل‌ها/پارامترها برای هر ۱۰ ارز
- [ ] بررسی دستی گزارش‌های بک‌تست اولیه قبل از فعال‌سازی کرون ساعتی
- [ ] دوره‌ی مشاهده‌ی paper trading (بدون سرمایه‌ی واقعی) پیشنهاد می‌شود
