# config.py
# تنظیمات مرکزی سیستم معاملاتی

# --- کلیدهای API ---
KUCOIN_API_KEY = "your_api_key_here"
KUCOIN_API_SECRET = "your_api_secret_here"
KUCOIN_API_PASSPHRASE = "your_passphrase_here"

# --- تنظیمات پلتفرم ---
EXCHANGE = "kucoin"
SANDBOX_MODE = False  # True برای تست، False برای LIVE

# --- تنظیمات معامله ---
DEFAULT_SYMBOL = "BTC-USDT"
DEFAULT_TIMEFRAME = "1h"
CAPITAL = 10000  # دلار
MAX_RISK_PER_TRADE = 0.02  # 2% ریسک در هر معامله
LEVERAGE = 1

# --- تنظیمات بک‌تست ---
BACKTEST_START_DATE = "2024-01-01"
BACKTEST_END_DATE = "2024-06-01"

# --- تنظیمات تلگرام ---
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token"
TELEGRAM_CHAT_ID = "your_telegram_chat_id"

# --- تنظیمات فیلترها ---
MIN_VOLUME_RATIO = 1.5  # فقط معامله با حجم بالاتر از میانگین 20 روزه
MIN_CONFIDENCE = 0.5     # حداقل اعتماد مدل برای تولید سیگنال
