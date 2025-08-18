from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

def prepare_data_for_xgboost(df, feature_cols):
    X = df[feature_cols]
    y = df['target']
    return X, y

def train_xgboost(X_train, y_train):
    # اعتبارسنجی کلاس‌ها
    if not set(y_train.unique()) <= {0, 1, 2}:
        raise ValueError("y must be in range [0, 1, 2]")
    
    model = XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1)
    model.fit(X_train, y_train)
    return model
