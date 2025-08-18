# تنظیمات کلی
SYMBOLS = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]
TIMEFRAME = "15min"
CANDLES_LIMIT = 500  # برای بک‌تست و آموزش
TEST_SIZE = 0.2       # 20% داده برای تست

# مدل‌ها
LSTM_LOOKBACK = 50     # تعداد کندل برای ورودی LSTM
XGBOOST_N_ESTIMATORS = 100

# مدیریت ریسک
RISK_REWARD_RATIO = 2   # حد سود = 2 × حد ضرر
ATR_MULTIPLIER_SL = 1.5 # حد ضرر = 1.5 × ATR
INITIAL_CAPITAL = 10000

# تلگرام (اختیاری)
TELEGRAM_TOKEN = ""  # ← اگر دارید، پر کنید
TELEGRAM_CHAT_ID = ""
SEND_TELEGRAM = bool(TELEGRAM_TOKEN and TELEGRAM_CHAT_ID)
