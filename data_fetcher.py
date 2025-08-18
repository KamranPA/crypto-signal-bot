import requests
import pandas as pd
from datetime import datetime

def fetch_kucoin(symbol, timeframe="15min", start_date=None, end_date=None):
    def date_to_ts(date_str):
        try:
            return int(datetime.strptime(date_str, "%Y-%m-%d").timestamp())
        except Exception as e:
            print(f'❌ فرمت تاریخ نامعتبر: {date_str}')
            return None

    url = "https://api.kucoin.com/api/v1/market/candles"
    params = {
        "symbol": symbol,
        "type": timeframe
    }

    if start_date:
        ts = date_to_ts(start_date)
        if ts:
            params["startAt"] = ts
    if end_date:
        ts = date_to_ts(end_date)
        if ts:
            params["endAt"] = ts

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data["code"] == "200000":
            if not data["data"]:
                print(f'⚠️ داده‌ای برای {symbol} در بازه زمانی یافت نشد.')
                return None

            df = pd.DataFrame(data["data"],
                              columns=["timestamp", "open", "close", "high", "low", "volume", "turnover"])
            df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit='s')
            df.set_index("timestamp", inplace=True)
            for col in ["open", "close", "high", "low", "volume"]:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df.sort_index(inplace=True)
            return df
        else:
            print(f'❌ خطای KuCoin: {data["msg"]}')
            return None
    except Exception as e:
        print(f'❌ خطا در دریافت داده: {e}')
        return None
