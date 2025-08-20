import numpy as np
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

def prepare_data_for_xgboost(df, feature_cols):
    """
    آماده‌سازی داده برای XGBoost
    """
    X = df[feature_cols]
    y = df['target']
    return X, y

def train_xgboost(X_train, y_train):
    """
    آموزش مدل XGBoost
    """
    if not set(y_train.unique()) <= {0, 1, 2}:
        raise ValueError("y_train must be in range [0, 1, 2]")
    model = XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1)
    model.fit(X_train, y_train)
    return model

def prepare_data_for_lstm(df, feature_cols, lookback=50):
    """
    آماده‌سازی داده برای LSTM
    - توجه: فقط ردیف‌هایی که اندیس >= lookback هستند، قابل استفاده هستند
    """
    if 'target' not in df.columns:
        print('❌ ستون "target" وجود ندارد. LSTM اجرا نمی‌شود.')
        return np.array([]), np.array([])

    X, y = [], []
    data = df[feature_cols].values
    target = df['target'].values

    # شروع از lookback تا انتهای داده
    for i in range(lookback, len(data)):
        X.append(data[i-lookback:i])
        y.append(target[i])

    X = np.array(X)
    y = np.array(y)

    if len(X) == 0:
        print('❌ داده کافی برای LSTM وجود ندارد (طول داده کمتر از lookback)')
        return np.array([]), np.array([])

    return X, y

def train_lstm(X_train, y_train, input_shape):
    """
    آموزش مدل LSTM
    """
    try:
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25),
            Dense(3, activation='softmax')
        ])
        model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        model.fit(X_train, y_train, epochs=10, batch_size=32, verbose=0)
        return model
    except Exception as e:
        print(f"❌ خطا در آموزش LSTM: {e}")
        return None
