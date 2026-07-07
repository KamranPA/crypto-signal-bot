# مسیر فایل: strategy/core.py
"""
منطق مشترک تولید سیگنال + محاسبه‌ی TP/SL.
این ماژول تنها جایی است که قانون "کی وارد معامله شویم و کجا خارج شویم" تعریف می‌شود.
هم backtest/engine.py و هم jobs/hourly_signal.py دقیقاً همین تابع را import می‌کنند
تا رفتار بک‌تست و لایو صد در صد یکسان باشد.
"""
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd

from features.indicators import compute_all_indicators


@dataclass
class Signal:
    timestamp: pd.Timestamp
    symbol: str
    direction: str          # "bull" یا "bear"
    entry: float
    stop_loss: float
    tp1: float
    tp2: float
    tp3: float


def generate_raw_signals(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    معادل دقیق منطق bull/bear در کد اصلی Pine Script:
      bull = crossover(close, supertrend) and macd>0 and macd>macd[1]
             and ema_fast>ema_slow and hma>hma[2] and donchian_trend>0
      bear = شرط متقارن
    """
    d = compute_all_indicators(df, params)

    cross_over = (d["close"].shift(1) <= d["supertrend"].shift(1)) & (d["close"] > d["supertrend"])
    cross_under = (d["close"].shift(1) >= d["supertrend"].shift(1)) & (d["close"] < d["supertrend"])

    macd_rising = d["macd"] > d["macd"].shift(1)
    macd_falling = d["macd"] < d["macd"].shift(1)
    hma_rising = d["hma"] > d["hma"].shift(2)
    hma_falling = d["hma"] < d["hma"].shift(2)

    d["bull"] = (
        cross_over
        & (d["macd"] > 0) & macd_rising
        & (d["ema_fast"] > d["ema_slow"])
        & hma_rising
        & (d["donchian_trend"] > 0)
    )
    d["bear"] = (
        cross_under
        & (d["macd"] < 0) & macd_falling
        & (d["ema_fast"] < d["ema_slow"])
        & hma_falling
        & (d["donchian_trend"] < 0)
    )
    return d


def compute_tp_sl(entry: float, direction: str, atr_value: float, risk_params: dict) -> dict:
    """معادل منطق atrStop / tp1_y / tp2_y / tp3_y در کد اصلی."""
    atr_band = atr_value * risk_params["atr_mult"]
    if direction == "bull":
        stop_loss = entry - atr_band
        risk = entry - stop_loss
        tp1 = entry + risk * risk_params["tp1_r"]
        tp2 = entry + risk * risk_params["tp2_r"]
        tp3 = entry + risk * risk_params["tp3_r"]
    else:
        stop_loss = entry + atr_band
        risk = stop_loss - entry
        tp1 = entry - risk * risk_params["tp1_r"]
        tp2 = entry - risk * risk_params["tp2_r"]
        tp3 = entry - risk * risk_params["tp3_r"]

    return {"stop_loss": stop_loss, "tp1": tp1, "tp2": tp2, "tp3": tp3}


def build_signal(df_with_indicators: pd.DataFrame, idx: int, symbol: str, risk_params: dict) -> Signal | None:
    """یک سیگنال کامل (با TP/SL) برای ردیف idx می‌سازد، اگر bull یا bear باشد."""
    row = df_with_indicators.iloc[idx]
    if row.get("bull"):
        direction = "bull"
    elif row.get("bear"):
        direction = "bear"
    else:
        return None

    levels = compute_tp_sl(row["close"], direction, row["atr14"], risk_params)
    return Signal(
        timestamp=df_with_indicators.index[idx],
        symbol=symbol,
        direction=direction,
        entry=row["close"],
        stop_loss=levels["stop_loss"],
        tp1=levels["tp1"],
        tp2=levels["tp2"],
        tp3=levels["tp3"],
    )
