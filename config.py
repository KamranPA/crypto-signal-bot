# تنظیمات کلی
SYMBOLS = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]
TIMEFRAME = "15min"
CANDLES_LIMIT = 500

# مدل‌ها
LSTM_LOOKBACK = 50
XGBOOST_N_ESTIMATORS = 100

# مدیریت ریسک
RISK_REWARD_RATIO = 2
ATR_MULTIPLIER_SL = 1.5
INITIAL_CAPITAL = 10000

# تلگرام — فقط برای تعیین فعال بودن ارسال
# توکن و چت آی‌دی از محیط (secrets) می‌آید
SEND_TELEGRAM = True  # فقط اگر secrets تنظیم شود، ارسال می‌شود
