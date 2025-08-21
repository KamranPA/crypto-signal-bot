import pandas as pd
import numpy as np
import ta

def add_features(df):
    df = df.copy()

    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_hist'] = macd.macd_diff()

    bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    df['bb_middle'] = bb.bollinger_mavg()

    df['atr'] = ta.volatility.AverageTrueRange(
        df['high'], df['low'], df['close'], window=14
    ).average_true_range()

    df['volume_change'] = df['volume'].pct_change()
    df['price_change_5'] = df['close'].pct_change(5)

    df['target_up'] = (df['close'].shift(-3) >= df['close'] * 1.01).astype(int)
    df['target_down'] = (df['close'].shift(-3) <= df['close'] * 0.99).astype(int)
    df['target'] = np.where(df['target_up'] == 1, 2,
                   np.where(df['target_down'] == 1, 0, 1))

    return df.dropna()
