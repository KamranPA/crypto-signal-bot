import pandas as pd
import numpy as np
from models import train_xgboost, prepare_data_for_xgboost, train_lstm, prepare_data_for_lstm
from risk import dynamic_stop_loss

class Backtester:
    def __init__(self, symbol, df, capital=10000):
        self.symbol = symbol
        self.df = df
        self.capital = capital
        self.results = []

    def run(self):
        # ویژگی‌های مورد استفاده
        feature_cols = ['rsi', 'macd', 'macd_signal', 'macd_hist', 'bb_upper', 'bb_lower',
                        'atr', 'volume_change', 'price_change_5', 'close', 'high', 'low', 'open']
        
        X = self.df[feature_cols]
        y = self.df['target']

        # تقسیم داده: 80% آموزش، 20% تست
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

        # داده تست
        test_df = self.df.iloc[split_idx:].copy()
        test_df['xgb_pred'] = xgb_pred
        test_df['lstm_pred'] = lstm_pred_classes[:len(test_df)]
        test_df['ml_avg'] = (test_df['xgb_pred'] + test_df['lstm_pred']) / 2

        # تبدیل 0,1,2 به -1,0,1
        class_to_signal = {0: -1, 1: 0, 2: 1}
        test_df['xgb_sig'] = test_df['xgb_pred'].map(class_to_signal)
        test_df['lstm_sig'] = test_df['lstm_pred'].map(class_to_signal)

        # محاسبه میانگین‌ها و اندیکاتورها در سطح داده (نه سطری)
        test_df['volume_ma20'] = test_df['volume'].rolling(20).mean()
        test_df['ma50'] = test_df['close'].rolling(50).mean()
        test_df['macd_hist_diff'] = test_df['macd_hist'].diff().fillna(0)

        # حذف مقادیر nan
        test_df.dropna(inplace=True)

        # فیلتر سیگنال‌ها
        signals = []
        for i, row in test_df.iterrows():
            # فیلتر ۱: روند صعودی (بالاتر از MA50 و BB Middle)
            if row['close'] < max(row['ma50'], row['bb_middle']):
                signals.append(0)
                continue

            # فیلتر ۲: حجم بالا (بالاتر از میانگین 20)
            if row['volume'] < row['volume_ma20']:
                signals.append(0)
                continue

            # فیلتر ۳: سیگنال تکنیکال
            ta_signal = 0
            if (row['rsi'] > 35 and row['rsi'] < 65 and
                row['macd_hist'] > 0 and row['macd_hist_diff'] > 0 and
                row['close'] < row['bb_upper']):
                ta_signal = 1
            elif (row['rsi'] < 65 and row['rsi'] > 35 and
                  row['macd_hist'] < 0 and row['close'] >= row['bb_upper']):
                ta_signal = -1

            if ta_signal == 0:
                signals.append(0)
                continue

            # فیلتر ۴: اطمینان مدل (فقط سیگنال‌های قوی)
            ml_confidence = abs(row['ml_avg'] - 1) if ta_signal == 1 else abs(row['ml_avg'] + 1)
            if ml_confidence < 1.3:  # حداقل اطمینان
                signals.append(0)
                continue

            signals.append(ta_signal)

        test_df['signal'] = signals

        # معکوس کردن target برای win_rate
        target_to_signal = {0: -1, 1: 0, 2: 1}
        test_df['actual'] = test_df['target'].map(target_to_signal)

        # محاسبه بازده
        test_df['return'] = test_df['close'].pct_change().shift(-1)  # بازده کندل بعدی
        test_df['strategy_return'] = test_df['return'] * test_df['signal'].shift(1).fillna(0)
        test_df['strategy_return'] = test_df['strategy_return'].fillna(0)

        # معیارهای ارزیابی
        win_rate = (test_df['signal'] == test_df['actual']).mean()
        total_return = (test_df['strategy_return'] + 1).prod() - 1
        sharpe = test_df['strategy_return'].mean() / (test_df['strategy_return'].std() + 1e-8) * np.sqrt(252)
        cumulative = (test_df['strategy_return'] + 1).cumprod()
        max_drawdown = (cumulative / cumulative.cummax() - 1).min()

        # میانگین سود و ضرر
        wins = test_df[test_df['strategy_return'] > 0]['strategy_return']
        losses = test_df[test_df['strategy_return'] < 0]['strategy_return']
        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 0
        reward_risk_ratio = avg_win / avg_loss if avg_loss != 0 else float('inf')

        # نتیجه نهایی
        result = {
            "symbol": self.symbol,
            "win_rate": win_rate,
            "sharpe": sharpe,
            "max_drawdown": max_drawdown,
            "total_return": total_return,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "reward_risk_ratio": reward_risk_ratio,
            "total_trades": len(test_df[test_df['signal'] != 0]),
            "positive_trades": (test_df['signal'] == test_df['actual']).sum(),
            "last_signal": signals[-1] if len(signals) > 0 else 0
        }
        return result
