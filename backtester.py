import pandas as pd
import numpy as np  # ← اضافه شد!
from models import train_xgboost, prepare_data_for_xgboost, train_lstm, prepare_data_for_lstm

class Backtester:
    def __init__(self, symbol, df):
        self.symbol = symbol
        self.df = df
        self.results = []

    def run(self):
        feature_cols = ['rsi', 'macd', 'macd_signal', 'macd_hist', 'bb_upper', 'bb_lower',
                        'atr', 'volume_change', 'price_change_5', 'close', 'high', 'low', 'open']
        X = self.df[feature_cols]
        y = self.df['target']

        # تقسیم داده
        split_idx = int(len(X) * (1 - 0.2))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # آموزش XGBoost
        xgb_model = train_xgboost(X_train, y_train)
        xgb_pred = xgb_model.predict(X_test)

        # آموزش LSTM
        X_train_lstm, y_train_lstm = prepare_data_for_lstm(X_train, feature_cols, 50)
        X_test_lstm, y_test_lstm = prepare_data_for_lstm(X_test, feature_cols, 50)

        if len(X_train_lstm) > 0 and len(X_test_lstm) > 0:
            lstm_model = train_lstm(X_train_lstm, y_train_lstm, (X_train_lstm.shape[1], X_train_lstm.shape[2]))
            lstm_pred = lstm_model.predict(X_test_lstm)
            lstm_pred_classes = np.argmax(lstm_pred, axis=1)
        else:
            lstm_pred_classes = [1] * len(y_test)  # خنثی

        # ترکیب سیگنال
        test_df = self.df.iloc[split_idx:].copy()
        test_df['xgb_pred'] = xgb_pred
        test_df['lstm_pred'] = lstm_pred_classes[:len(test_df)]
        test_df['ml_avg'] = (test_df['xgb_pred'] + test_df['lstm_pred']) / 2

        # تبدیل 0,1,2 به -1,0,1
        class_to_signal = {0: -1, 1: 0, 2: 1}
        test_df['xgb_sig'] = test_df['xgb_pred'].map(class_to_signal)
        test_df['lstm_sig'] = test_df['lstm_pred'].map(class_to_signal)

        # فیلتر تکنیکال
        signals = []
        for i, row in test_df.iterrows():
            ml_signal = 1 if row['ml_avg'] > 1.3 else (-1 if row['ml_avg'] < 0.7 else 0)
            ta_signal = 0
            if row['rsi'] < 30 and row['macd_hist'] > 0:
                ta_signal = 1
            elif row['rsi'] > 70 and row['close'] >= row['bb_upper']:
                ta_signal = -1

            final_signal = 0.7 * ml_signal + 0.3 * ta_signal
            signals.append(np.sign(final_signal))  # ← np اکنون تعریف شده

        test_df['signal'] = signals

        # معکوس کردن target برای win_rate
        target_to_signal = {0: -1, 1: 0, 2: 1}
        test_df['actual'] = test_df['target'].map(target_to_signal)
        win_rate = (test_df['signal'] == test_df['actual']).mean()

        # محاسبه معیارها
        sharpe = (test_df['close'].pct_change().mean() * 252) / (test_df['close'].pct_change().std() * np.sqrt(252))
        max_drawdown = (test_df['close'] / test_df['close'].cummax() - 1).min()

        result = {
            "symbol": self.symbol,
            "win_rate": win_rate,
            "sharpe": sharpe,
            "max_drawdown": max_drawdown,
            "total_trades": len(test_df),
            "positive_trades": (test_df['signal'] == test_df['actual']).sum(),
            "last_signal": signals[-1]
        }
        return result
