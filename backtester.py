import pandas as pd
import numpy as np
from models import train_xgboost, prepare_data_for_xgboost, train_lstm, prepare_data_for_lstm

class Backtester:
    def __init__(self, symbol, df):
        self.symbol = symbol
        self.df = df

    def run(self):
        # ویژگی‌ها
        feature_cols = ['rsi', 'macd', 'macd_signal', 'macd_hist', 'bb_upper', 'bb_lower',
                        'atr', 'volume_change', 'price_change_5', 'close', 'high', 'low', 'open']
        
        X = self.df[feature_cols]
        y = self.df['target']

        split_idx = int(len(X) * (1 - 0.2))
        if split_idx < 50:
            return self.empty_result()

        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # آموزش XGBoost
        try:
            xgb_model = train_xgboost(X_train, y_train)
            xgb_pred = xgb_model.predict(X_test)
        except Exception as e:
            print(f"❌ خطا در آموزش XGBoost: {e}")
            return self.empty_result()

        # آموزش LSTM
        X_train_lstm, y_train_lstm = prepare_data_for_lstm(X_train, feature_cols, 50)
        X_test_lstm, y_test_lstm = prepare_data_for_lstm(X_test, feature_cols, 50)

        if len(X_train_lstm) > 0 and len(X_test_lstm) > 0:
            try:
                lstm_model = train_lstm(X_train_lstm, y_train_lstm, (X_train_lstm.shape[1], X_train_lstm.shape[2]))
                lstm_pred = lstm_model.predict(X_test_lstm)
                lstm_pred_classes = np.argmax(lstm_pred, axis=1)
            except Exception as e:
                print(f"❌ خطا در آموزش LSTM: {e}")
                lstm_pred_classes = [1] * len(y_test)
        else:
            lstm_pred_classes = [1] * len(y_test)

        # داده تست
        test_df = self.df.iloc[split_idx:].copy()
        if test_df.empty:
            print(f"❌ داده‌های تست برای {self.symbol} خالی است.")
            return self.empty_result()

        # افزودن پیش‌بینی‌ها
        test_df['xgb_pred'] = xgb_pred
        test_df['lstm_pred'] = lstm_pred_classes[:len(test_df)]
        test_df['ml_avg'] = (test_df['xgb_pred'] + test_df['lstm_pred']) / 2

        # تولید سیگنال ML
        signals = []
        for i, row in test_df.iterrows():
            ml_signal = 1 if row['ml_avg'] > 1.3 else (-1 if row['ml_avg'] < 0.7 else 0)
            signals.append(ml_signal)

        # دیباگ: بررسی طول
        print(f"📊 طول test_df: {len(test_df)}")
        print(f"📊 طول signals: {len(signals)}")

        # تنظیم طول signals
        if len(signals) < len(test_df):
            signals = [0] * (len(test_df) - len(signals)) + signals

        test_df['signal'] = signals

        # دیباگ: بررسی تنوع سیگنال
        unique_signals, counts = np.unique(signals, return_counts=True)
        signal_counts = dict(zip(unique_signals, counts))
        print(f"📊 سیگنال‌های {self.symbol}: {signal_counts}")

        if len(unique_signals) == 1 and unique_signals[0] == 0:
            print(f"⚠️ هشدار: سیگنال همیشه 0 است — مدل بایاس شده")
            return self.empty_result()

        # معکوس کردن target
        target_to_signal = {0: -1, 1: 0, 2: 1}
        test_df['actual'] = test_df['target'].map(target_to_signal)

        # محاسبه بازده
        test_df['return'] = test_df['close'].pct_change().shift(-1)
        test_df['strategy_return'] = test_df['return'] * test_df['signal'].shift(1).fillna(0)
        test_df['strategy_return'] = test_df['strategy_return'].fillna(0)

        # فقط معاملات معتبر
        valid_trades = test_df[test_df['signal'] != 0]
        if len(valid_trades) == 0:
            print(f"❌ هیچ معامله معتبری برای {self.symbol} وجود ندارد.")
            return self.empty_result()

        # محاسبه معیارها
        win_rate = (valid_trades['signal'] == valid_trades['actual']).mean()
        total_return = (valid_trades['strategy_return'] + 1).prod() - 1
        sharpe = valid_trades['strategy_return'].mean() / (valid_trades['strategy_return'].std() + 1e-8) * np.sqrt(252)
        cumulative = (valid_trades['strategy_return'] + 1).cumprod()
        max_drawdown = (cumulative / cumulative.cummax() - 1).min()

        wins = valid_trades[valid_trades['strategy_return'] > 0]['strategy_return']
        losses = valid_trades[valid_trades['strategy_return'] < 0]['strategy_return']
        avg_win = wins.mean() if len(wins) > 0 else 0.0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 0.0
        reward_risk_ratio = avg_win / avg_loss if avg_loss != 0 else float('inf')

        result = {
            "symbol": self.symbol,
            "win_rate": win_rate,
            "sharpe": sharpe,
            "max_drawdown": max_drawdown,
            "total_return": total_return,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "reward_risk_ratio": reward_risk_ratio,
            "total_trades": len(valid_trades),
            "positive_trades": (valid_trades['signal'] == valid_trades['actual']).sum(),
            "last_signal": signals[-1] if len(signals) > 0 else 0
        }
        return result

    def empty_result(self):
        return {
            "symbol": self.symbol,
            "win_rate": 0.0,
            "sharpe": 0.0,
            "max_drawdown": 0.0,
            "total_return": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "reward_risk_ratio": float('inf'),
            "total_trades": 0,
            "positive_trades": 0,
            "last_signal": 0
        }
