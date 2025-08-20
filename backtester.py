# backtester.py — نسخه نهایی با نمودار معاملات

import pandas as pd
import numpy as np
from models import prepare_data_for_xgboost, prepare_data_for_lstm

class Backtester:
    def __init__(self, symbol, df):
        self.symbol = symbol
        self.df = df

    def run(self):
        feature_cols = ['rsi', 'macd', 'macd_signal', 'macd_hist', 'bb_upper', 'bb_lower',
                        'atr', 'volume_change', 'price_change_5', 'close', 'high', 'low', 'open']
        
        X = self.df[feature_cols]

        split_idx = int(len(X) * (1 - 0.2))
        if split_idx < 50:
            return self.empty_result()

        X_train, X_test = X[:split_idx], X[split_idx:]

        # --- XGBoost: بدون آموزش ---
        xgb_pred = np.random.choice([0, 1, 2], size=len(X_test))  # سیگنال تصادفی

        # --- LSTM: بدون آموزش ---
        X_train_lstm, _ = prepare_data_for_lstm(X_train, feature_cols, 50)
        X_test_lstm, _ = prepare_data_for_lstm(X_test, feature_cols, 50)

        if len(X_train_lstm) > 0 and len(X_test_lstm) > 0:
            lstm_pred_classes = np.random.choice([0, 1, 2], size=len(X_test_lstm))  # سیگنال تصادفی
        else:
            lstm_pred_classes = np.random.choice([0, 1, 2], size=len(X_test))

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

        test_df['signal'] = signals

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
            "win_rate": 0.0,
            "sharpe": sharpe,
            "max_drawdown": max_drawdown,
            "total_return": total_return,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "reward_risk_ratio": reward_risk_ratio,
            "total_trades": len(valid_trades),
            "positive_trades": 0,
            "last_signal": signals[-1] if len(signals) > 0 else 0
        }

        # ✅ رسم نمودار معاملات (در صورت وجود matplotlib)
        self.plot_trades(test_df, result)

        return result

    def plot_trades(self, test_df, result):
        try:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(test_df.index, test_df['close'], label='قیمت', color='blue')

            # نمایش سیگنال‌ها
            buy_signals = test_df[test_df['signal'] == 1]
            sell_signals = test_df[test_df['signal'] == -1]

            ax.scatter(buy_signals.index, buy_signals['close'], color='green', marker='^', s=100, label='خرید')
            ax.scatter(sell_signals.index, sell_signals['close'], color='red', marker='v', s=100, label='فروش')

            ax.set_title(f'شبیه‌سازی معاملات: {self.symbol}')
            ax.set_xlabel('زمان')
            ax.set_ylabel('قیمت')
            ax.legend()
            plt.tight_layout()
            plt.savefig(f'{self.symbol.replace("/", "_")}_trades.png')
            plt.close()
            print(f"✅ نمودار معاملات ذخیره شد: {self.symbol.replace('/', '_')}_trades.png")
        except ImportError:
            print("❌ matplotlib نصب نیست — نمودار تولید نشد")
        except Exception as e:
            print(f"❌ خطای رسم نمودار: {e}")

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
