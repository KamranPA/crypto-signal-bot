# src/data/data_fetcher.py

import pandas as pd
import requests
from datetime import datetime
import json

# 🔥 نگاشت صحیح تایم‌فریم‌ها به فرمت دقیق CoinEx
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
    """
    print(f"🔍 Debug: دریافت داده برای {symbol}, تایم‌فریم={timeframe}, شروع={start_date}, پایان={end_date}")

    # 1. تبدیل نماد: BTC/USDT → BTCUSDT
    market = symbol.replace("/", "").upper()
    print(f"✅ market: {market}")

    # 2. تبدیل تایم‌فریم به فرمت صحیح CoinEx
    if timeframe.lower() not in TIMEFRAME_MAP:
        print(f"❌ خطای تایم‌فریم: '{timeframe}'. مجاز: {list(TIMEFRAME_MAP.keys())}")
        return pd.DataFrame()

    interval = TIMEFRAME_MAP[timeframe.lower()]
    print(f"✅ interval: {interval}")

    # 3. تبدیل تاریخ به ثانیه
    try:
        start_timestamp = int(pd.to_datetime(start_date).timestamp())
        end_timestamp = int(pd.to_datetime(end_date).timestamp())
        print(f"✅ start_timestamp: {start_timestamp}")
        print(f"✅ end_timestamp: {end_timestamp}")
    except Exception as e:
        print(f"❌ خطای تاریخ: {e}")
        return pd.DataFrame()

    # 4. URL API CoinEx
    url = "https://api.coinex.com/v1/market/kline"
    print(f"✅ URL: {url}")

    all_data = []
    current_start = start_timestamp

    while current_start < end_timestamp:
        # محدودیت: حداکثر 30 روز در هر درخواست
        max_to = current_start + 3600 * 24 * 30  # 30 روز
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
                break

            all_data.extend(klines)

            last_timestamp = klines[-1][0]
            if last_timestamp <= current_start:
                break
            current_start = last_timestamp + 1

        except Exception as e:
            print(f"❌ خطا در ارتباط: {e}")
            return pd.DataFrame()

        # جلوگیری از rate limit
        time.sleep(0.1)

    if not all_data:
        print(f"❌ هیچ داده‌ای برای {symbol} در تایم‌فریم {timeframe} دریافت نشد.")
        return pd.DataFrame()

    # ساخت دیتافریم
    df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'amount'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    df = df.astype({
        'open': 'float64',
        'high': 'float64',
        'low': 'float64',
        'close': 'float64',
        'volume': 'float64'
    })
    df = df.set_index('timestamp')
    df = df.sort_index()

    # فیلتر بر اساس بازه زمانی
    df = df.loc[start_date:end_date]
    print(f"✅ داده نهایی: {df.shape[0]} کندل")

    return df
