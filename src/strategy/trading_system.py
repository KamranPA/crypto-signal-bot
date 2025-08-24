# src/strategy/trading_system.py
from src.regime_detection.range_detector import is_range_regime
from src.regime_detection.trend_detector import is_trend_regime
from src.regime_detection.breakout_detector import is_breakout_regime
import ta

def generate_signal(df):
    if len(df) < 50:
        return {'signal': None, 'regime': 'Insufficient Data'}

    # محاسبه شاخص‌ها
    df['ema_21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
    df['atr'] = ta.volatility.AverageTrueRange(
        df['high'], df['low'], df['close'], window=14
    ).average_true_range()

    # محاسبه ADX
    adx_indicator = ta.trend.ADXIndicator(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=14
    )
    df.loc[:, 'adx'] = adx_indicator.adx()
    adx_value = df['adx'].iloc[-1]

    last = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]
    atr = last['atr']

    # فیلتر حجم
    volume_avg = df['volume'].rolling(20).mean().iloc[-1]
    volume_ratio = last['volume'] / volume_avg

    in_trend = is_trend_regime(df)
    in_range = is_range_regime(df)
    in_breakout = is_breakout_regime(df)

    signal = entry = sl = tp = None
    regime = 'Uncertain'
