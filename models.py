# models.py — نسخه بدون target

import numpy as np
from xgboost import XGBClassifier
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

def prepare_data_for_xgboost(df, feature_cols):
    X = df[feature_cols]
    return X  # بدون y

def train_xgboost(X_train, y_train=None):
    # بدون آموزش — فقط سیگنال تصادفی یا خنثی
    print("⚠️ XGBoost بدون آموزش (target حذف شد)")
    return None

def prepare_data_for_lstm(df, feature_cols, lookback=50):
    X, y = [], []
    data = df[feature_cols].values
    for i in range(lookback, len(data)):
        X.append(data[i-lookback:i])
    return np.array(X), np.array([])  # بدون y

def train_lstm(X_train, y_train=None, input_shape=None):
    # بدون آموزش — فقط مدل ساخته می‌شود
    print("⚠️ LSTM بدون آموزش (target حذف شد)")
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=input_shape),
        Dropout(0.2),
        LSTM(50, return_sequences=False),
        Dropout(0.2),
        Dense(25),
        Dense(3, activation='softmax')
    ])
    # بدون fit()
    return model
