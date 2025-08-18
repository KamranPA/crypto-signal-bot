import requests
import pandas as pd

def fetch_kucoin(symbol, timeframe="15min", limit=200):
    url = "https://api.kucoin.com/api/v1/market/candles"
    params = {
        "symbol": symbol,
        "type": timeframe,
        "limit": limit
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data["code"] == "200000":
            df = pd.DataFrame(data["data"], 
                              columns=["timestamp", "open", "close", "high", "low", "volume", "turnover"])
            df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit='s')
            df.set_index("timestamp", inplace=True)
            for col in ["open", "close", "high", "low", "volume"]:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df.sort_index(inplace=True)
            return df
        else:
            print(f"Error: {data['msg']}")
            return None
    except Exception as e:
        print(f"Fetch error: {e}")
        return None
