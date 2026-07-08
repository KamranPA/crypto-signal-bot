# مسیر فایل: strategy/core.py
"""
منطق مشترک تولید سیگنال + محاسبه‌ی TP/SL.
این ماژول تنها جایی است که قانون "کی وارد معامله شویم و کجا خارج شویم" تعریف می‌شود.
هم backtest/engine.py و هم jobs/hourly_signal.py دقیقاً همین تابع را import می‌کنند
تا رفتار بک‌تست و لایو صد در صد یکسان باشد (مطابق architecture.md بخش ۳).
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
    معادل دقیق منطق bull/bear در کد اصلی Pine Script.

    نکته‌ی مهم: در کد اصلی، `Presets` هاردکد است روی "All Signals" (ورودی کاربرش
    کامنت شده). با این مقدار، فرمول واقعی bull/bear به این شکل ساده می‌شود:

        bull = crossover(close, supertrend)
               and (StrongSignalsOnly ? close>StrongFilter : true)   -> پیش‌فرض false → true
               and (ContrarianOnly    ? ContBull            : true)   -> پیش‌فرض false → true
               and (consSignalsFilter ? adx>20               : true)  -> پیش‌فرض true (چون
                                                                          filterstyle پیش‌فرض
                                                                          "Trending Signals [Mode]")
               and (highVolSignals    ? volFilter            : true)  -> پیش‌فرض false → true
               and (signalsTrendCloud ? ...                  : true)  -> پیش‌فرض false → true

    یعنی سیگنال پیش‌فرض واقعی فقط «Supertrend crossover + ADX > adx_threshold» است.
    شرایط MACD/EMA150-250/HMA rising/Donchian (که در نسخه‌ی قبلی این تابع اشتباهاً
    اینجا اعمال شده بودند) در کد اصلی متعلق به confBull/confBear هستند — متغیرهایی
    که فقط برای preset دیگری به‌نام "Strong+" استفاده می‌شوند و در این پیکربندی
    (Presets == "All Signals" ثابت) هرگز در مسیر اجرا قرار نمی‌گیرند.
    """
    d = compute_all_indicators(df, params)
    adx_threshold = params["indicator"]["adx_threshold"]

    cross_over = (d["close"].shift(1) <= d["supertrend"].shift(1)) & (d["close"] > d["supertrend"])
    cross_under = (d["close"].shift(1) >= d["supertrend"].shift(1)) & (d["close"] < d["supertrend"])

    cons_filter = d["adx"] > adx_threshold

    d["bull"] = cross_over & cons_filter
    d["bear"] = cross_under & cons_filter
    return d


def compute_tp_sl(entry: float, direction: str, atr_value: float, risk_params: dict) -> dict:
    """
    معادل منطق atrStop / tp1_y / tp2_y / tp3_y در کد اصلی.
    risk_params شامل: atr_mult, tp1_r, tp2_r, tp3_r
    (این پارامترها هم می‌توانند baseline باشند هم خروجی بهینه‌سازی Optuna برای آن ارز خاص —
    ml/optimize.py مقدار per-coin را در param_history ذخیره و اینجا فقط مصرف می‌شود.)
    """
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
