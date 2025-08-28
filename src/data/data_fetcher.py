# src/data/data_fetcher.py

import ccxt
import pandas as pd

def fetch_data(symbol, timeframe, start_date, end_date):
    print(f"🔍 دریافت داده برای {symbol}, تایم‌فریم={timeframe}, بازه={start_date} تا {end_date}")
    
    exchange = ccxt.coinex({
        'enableRateLimit': True,
    })

    try:
        since = int(pd.to_datetime(start_date).timestamp() * 1000)
        end_ms = int(pd.to_datetime(end_date).timestamp() * 1000)
        all_data = []

        while since < end_ms:
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since, limit=1000)
                if not ohlcv:
                    break
                all_data.extend(ohlcv)
                since = ohlcv[-1][0] + 1
            except Exception as e:
                print(f"❌ خطا در دریافت داده: {e}")
                break

        if not all_
            print("❌ هیچ داده‌ای دریافت نشد.")
            return pd.DataFrame()

        df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.set_index('timestamp')
        df = df.loc[start_date:end_date]
        df = df.astype(float)
        print(f"✅ {len(df)} کندل دریافت شد.")
        return df

    except Exception as e:
        print(f"❌ خطای کلی در دریافت داده: {e}")
        return pd.DataFrame()
