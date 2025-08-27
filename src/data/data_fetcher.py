# src/data/data_fetcher.py

import pandas as pd
import requests
from datetime import datetime
import json

# نگاشت تایم‌فریم‌ها به فرمت CoinEx
TIMEFRAME_MAP = {
    '1m': '1m',
    '3m': '3m',
    '5m': '5m',
    '15m': '15m',
    '30m': '30m',
    '1h': '1H',
    '2h': '2H',
    '4h': '4H',
    '6h': '6H',
    '12h': '12H',
    '1d': '1D',
    '3d': '3D',
    '1w': '1W',
    '1M': '1M'
}

def fetch_data(symbol, timeframe, start_date, end_date):
    """
    دریافت داده کندلی از صرافی CoinEx
    """
    print(f"🔍 Debug: Fetching data for {symbol}, timeframe={timeframe}, start={start_date}, end={end_date}")

    # 1. تبدیل نماد: BTC/USDT → BTCUSDT
    market = symbol.replace("/", "").upper()
    print(f"✅ market: {market}")

    # 2. تبدیل تایم‌فریم به فرمت CoinEx
    if timeframe.lower() not in TIMEFRAME_MAP:
        print(f"❌ Error: Invalid timeframe '{timeframe}'. Supported: {list(TIMEFRAME_MAP.keys())}")
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
        print(f"❌ Error: Invalid date format. {e}")
        return pd.DataFrame()

    # 4. URL API CoinEx
    url = "https://api.coinex.com/v1/market/kline"
    print(f"✅ URL: {url}")

    all_data = []
    current_start = start_timestamp

    while current_start < end_timestamp:
        params = {
            'market': market,
            'type': interval,
            'limit': 1000,
            'from': current_start,
            'to': min(current_start + 3600 * 24 * 30, end_timestamp)  # حداکثر 30 روز
        }
        print(f"🔄 Request params: {json.dumps(params, ensure_ascii=False)}")

        try:
            response = requests.get(url, params=params, timeout=10)
            print(f"✅ Response status: {response.status_code}")
            print(f"✅ Response headers: {response.headers}")

            data = response.json()
            print(f"✅ Response body: {json.dumps(data, ensure_ascii=False, indent=2)}")

            if data.get('code') != 0:
                error_msg = data.get('message', 'Unknown error')
                print(f"❌ Error from CoinEx: code={data['code']}, message='{error_msg}'")
                return pd.DataFrame()

            klines = data['data']
            print(f"✅ Received {len(klines)} klines")

            if not klines:
                break

            all_data.extend(klines)

            last_timestamp = klines[-1][0]
            if last_timestamp <= current_start:
                break
            current_start = last_timestamp + 1

        except Exception as e:
            print(f"❌ Exception during request: {e}")
            return pd.DataFrame()

        time.sleep(0.1)  # جلوگیری از rate limit

    if not all_data:
        print(f"❌ No data received for {symbol} in {timeframe}")
        return pd.DataFrame()

    # 5. ساخت دیتافریم
    df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'amount'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    df = df.set_index('timestamp')
    df = df.sort_index()

    # 6. فیلتر بر اساس بازه زمانی
    df = df.loc[start_date:end_date]
    print(f"✅ Final DataFrame shape: {df.shape}")

    return df
