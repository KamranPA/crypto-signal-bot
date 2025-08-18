# models.py
import numpy as np
import pandas as pd
from xgboost import XGBClassifier  # ← تغییر کردیم!
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

def prepare_data_for_xgboost(df, feature_cols):
    X = df[feature_cols]
    y = df['target']
    return X, y

def train_xgboost(X_train, y_train):
    model = XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1)
    model.fit(X_train, y_train)
    return model

def prepare_data_for_lstm(df, feature_cols, lookback=50):
    X, y = [], []
    data = df[feature_cols].values
    target = df['target'].values
    for i in range(lookback, len(data)):
        X.append(data[i-lookback:i])
        y.append(target[i])
    return np.array(X), np.array(y)

def train_lstm(X_train, y_train, input_shape):
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=input_shape),
        Dropout(0.2),
        LSTM(50, return_sequences=False),
        Dropout(0.2),
        Dense(25),
        Dense(3, activation='softmax')
    ])
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    y_train = y_train + 1  # -1,0,1 → 0,1,2
    model.fit(X_train, y_train, epochs=10, batch_size=32, verbose=0)
    return model

def get_sentiment_score():
    import random
    return random.uniform(-1, 1)
