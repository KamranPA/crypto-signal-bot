# features.py — نسخه اصلاح‌شده (هدف تکنیکال)

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

    # 🎯 هدف جدید: سیگنال تکنیکال (نه حرکت قیمت)
    buy_signal = (
        (df['rsi'] > 30) & (df['rsi'] < 60) &
        (df['macd_hist'] > 0) & (df['macd_hist'] > df['macd_hist'].shift(1)) &
        (df['close'] < df['bb_upper'])
    )
    sell_signal = (
        (df['rsi'] > 60) & (df['rsi'] < 70) &
        (df['macd_hist'] < 0) &
        (df['close'] >= df['bb_upper'])
    )

    # 🎯 تبدیل به target: 2=خرید، 0=فروش، 1=هیچکدام
    df['target'] = np.where(buy_signal, 2,
                   np.where(sell_signal, 0, 1))

    # دیباگ: چاپ توزیع target
    print("📊 توزیع target جدید:", df['target'].value_counts().to_dict())

    # اطمینان از وجود target
    if 'target' not in df.columns:
        raise ValueError("❌ ستون 'target' در داده وجود ندارد!")

    return df.dropna()
