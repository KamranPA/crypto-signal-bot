# features.py — نسخه اصلاح‌شده با تعادل target

import pandas as pd
import numpy as np
import ta

def add_features(df):
    df = df.copy()

    # RSI
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()

    # MACD
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_hist'] = macd.macd_diff()

    # Bollinger Bands
    bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    df['bb_middle'] = bb.bollinger_mavg()

    # ATR
    df['atr'] = ta.volatility.AverageTrueRange(
        df['high'], df['low'], df['close'], window=14
    ).average_true_range()

    # Volume Change
    df['volume_change'] = df['volume'].pct_change()

    # Price Change (5 candles ago)
    df['price_change_5'] = df['close'].pct_change(5)

    # 🎯 هدف: +1% در 3 کندل آینده؟
    df['target_up'] = (df['close'].shift(-3) >= df['close'] * 1.01).astype(int)
    # 🎯 هدف: -1% در 3 کندل آینده؟
    df['target_down'] = (df['close'].shift(-3) <= df['close'] * 0.99).astype(int)

    # 🎯 تبدیل به target: 2=صعودی، 0=نزولی، 1=خنثی
    df['target'] = np.where(df['target_up'] == 1, 2,
                   np.where(df['target_down'] == 1, 0, 1))

    # 🔁 حذف کلاس‌های نامتعادل (اگر خیلی زیاد هستند)
    class_counts = df['target'].value_counts()
    min_count = min(class_counts.get(0, 0), class_counts.get(1, 0), class_counts.get(2, 0))
    
    if min_count > 0:
        sampled = []
        for cls in [0, 1, 2]:
            cls_data = df[df['target'] == cls]
            if len(cls_data) > min_count:
                cls_data = cls_data.sample(n=min_count, random_state=42)
            sampled.append(cls_data)
        df = pd.concat(sampled).sort_index()

    # دیباگ: چاپ توزیع target بعد از تعادل
    print("📊 توزیع target بعد از تعادل:", df['target'].value_counts().to_dict())

    return df.dropna()
