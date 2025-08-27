# src/data/data_fetcher.py

import pandas as pd
import requests
import time
from datetime import datetime
import json

# نگاشت تایم‌فریم‌ها به فرمت دقیق CoinEx
TIMEFRAME_MAP = {
    '1m': '1min',
    '3m': '3min',
    '5m': '5min',
    '15m': '15min',
    '30m': '30min',
    '1h': '1hour',
    '2h': '2hour',
    '4h': '4hour',
    '6h': '6hour',
    '12h': '12hour',
    '1d': '1day',
    '3d': '3day',
    '1w': '1week',
    '1M': '1mon'
}

def fetch_data(symbol, timeframe, start_date, end_date):
    """
    دریافت داده کندلی از صرافی CoinEx
    
    ورودی:
        symbol: مثلاً "BTC/USDT"
        timeframe: مثلاً "1h"
        start_date: تاریخ شروع (رشته یا datetime)
        end_date: تاریخ پایان (رشته یا datetime)
    
    خروجی:
        دیتافریم با ستون‌های: timestamp, open, high, low, close, volume
        اگر خطا داشت یا داده‌ای نبود، یک دیتافریم خالی برمی‌گرداند
    """
    print(f"🔍 دریافت داده برای {symbol}, تایم‌فریم={timeframe}, بازه={start_date} تا {end_date}")

    # 1. تبدیل نماد: BTC/USDT → BTCUSDT
    market = symbol.replace("/", "").upper()
    print(f"✅ نماد: {market}")

    # 2. تبدیل تایم‌فریم به فرمت CoinEx
    if timeframe.lower() not in TIMEFRAME_MAP:
        print(f"❌ تایم‌فریم نامعتبر: '{timeframe}'. پشتیبانی: {list(TIMEFRAME_MAP.keys())}")
        return pd.DataFrame()

    interval = TIMEFRAME_MAP[timeframe.lower()]
    print(f"✅ تایم‌فریم: {interval}")

    # 3. تبدیل تاریخ به ثانیه
    try:
        start_timestamp = int(pd.to_datetime(start_date).timestamp())
        end_timestamp = int(pd.to_datetime(end_date).timestamp())
        print(f"✅ شروع: {start_timestamp} | پایان: {end_timestamp}")
    except Exception as e:
        print(f"❌ خطای تاریخ: {e}")
        return pd.DataFrame()

    # 4. URL API CoinEx
    url = "https://api.coinex.com/v1/market/kline"
    print(f"✅ URL: {url}")

    all_data = []
    current_start = start_timestamp

    # 5. دریافت داده به صورت صفحه‌بندی شده (حداکثر 30 روز در هر درخواست)
    while current_start < end_timestamp:
        max_to = current_start + 3600 * 24 * 30  # حداکثر 30 روز
        to = min(max_to, end_timestamp)
        print(f"🔄 درخواست: از {current_start} تا {to}")

        params = {
            'market': market,
            'type': interval,
            'limit': 1000,
            'from': current_start,
            'to': to
        }
        print(f"🔄 پارامترها: {json.dumps(params, ensure_ascii=False)}")

        try:
            response = requests.get(url, params=params, timeout=10)
            print(f"✅ وضعیت پاسخ: {response.status_code}")

            data = response.json()
            print(f"✅ پاسخ JSON: {json.dumps(data, ensure_ascii=False, indent=2)}")

            if data.get('code') != 0:
                error_msg = data.get('message', 'خطای ناشناخته')
                print(f"❌ خطای CoinEx: کد={data['code']}, پیام='{error_msg}'")
                return pd.DataFrame()

            klines = data['data']
            print(f"✅ {len(klines)} کندل دریافت شد")

            if not klines:
                break  # داده‌ای وجود ندارد

            all_data.extend(klines)

            # به‌روزرسانی زمان شروع برای درخواست بعدی
            last_timestamp = klines[-1][0]
            if last_timestamp <= current_start:
                break  # جلوگیری از حلقه بی‌نهایت
            current_start = last_timestamp + 1

        except Exception as e:
            print(f"❌ خطای ارتباط با CoinEx: {e}")
            return pd.DataFrame()

        # جلوگیری از محدودیت نرخ درخواست
        time.sleep(0.1)

    # 6. اگر داده‌ای دریافت نشد
    if not all_data:
        print(f"❌ هیچ داده‌ای برای {symbol} در تایم‌فریم {timeframe} یافت نشد.")
        return pd.DataFrame()

    # 7. ساخت دیتافریم
    df = pd.DataFrame(all_data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume', 'amount'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    df = df.set_index('timestamp')
    df = df.sort_index()

    # 8. فیلتر بر اساس بازه زمانی
    df = df.loc[start_date:end_date]
    print(f"✅ داده نهایی: {df.shape[0]} کندل")

    return df
