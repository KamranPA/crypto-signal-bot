# مسیر فایل: data/calibration.py
"""
هماهنگ‌سازی دیتای Yahoo Finance (بک‌تست بلندمدت) با CoinEx (منبع حقیقت برای Live).
مطابق architecture.md بخش ۲.۲.

قاعده‌ی طلایی: مدل نهایی Live فقط با CoinEx train/fine-tune می‌شود. این ماژول صرفاً
دیتای Yahoo را برای اعتبارسنجی کلی منطق استراتژی روی بازه‌ی بلندمدت‌تر قابل‌استفاده می‌کند.
"""
from __future__ import annotations
import pandas as pd
import numpy as np


def find_overlap(df_yahoo: pd.DataFrame, df_coinex: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp]:
    start = max(df_yahoo.index.min(), df_coinex.index.min())
    end = min(df_yahoo.index.max(), df_coinex.index.max())
    return start, end


def compute_calibration_ratio(df_yahoo: pd.DataFrame, df_coinex: pd.DataFrame) -> float:
    """
    میانگین نسبت close-to-close بین دو منبع در بازه‌ی هم‌پوشان.
    ratio > 1 یعنی CoinEx به‌طور میانگین بالاتر از Yahoo قیمت می‌دهد (و برعکس).
    """
    start, end = find_overlap(df_yahoo, df_coinex)
    if start >= end:
        return 1.0  # هیچ هم‌پوشانی‌ای نیست؛ بدون تعدیل

    y = df_yahoo.loc[start:end, "close"].resample("1h").ffill()
    c = df_coinex.loc[start:end, "close"].resample("1h").ffill()
    aligned = pd.concat([y, c], axis=1, keys=["yahoo", "coinex"]).dropna()

    if aligned.empty:
        return 1.0

    ratios = aligned["coinex"] / aligned["yahoo"]
    return float(ratios.median())  # median به‌جای mean برای مقاومت در برابر outlier


def calibrate_yahoo_to_coinex(df_yahoo: pd.DataFrame, ratio: float) -> pd.DataFrame:
    """اعمال ضریب تعدیل روی ستون‌های قیمتی (نه volume)."""
    out = df_yahoo.copy()
    for col in ["open", "high", "low", "close"]:
        out[col] = out[col] * ratio
    return out


def build_calibrated_history(df_yahoo: pd.DataFrame, df_coinex: pd.DataFrame) -> pd.DataFrame:
    """
    خروجی نهایی برای بک‌تست: بخش قدیمی از Yahoo (کالیبره‌شده) + بخش اخیر از CoinEx (خام).
    ستون 'source' برای شفافیت در گزارش بک‌تست حفظ می‌شود.

    مقاوم در برابر خالی بودن یکی از دو منبع (مثلاً وقتی Yahoo روی سرورهای GitHub Actions
    به‌طور موقت Rate-Limit می‌شود و دیتافریم خالی برمی‌گرداند). قبلاً این حالت باعث خطای
    NaT در محاسبه‌ی overlap می‌شد و کل ارز بی‌سروصدا از گزارش حذف می‌شد — رفع شد.
    """
    if df_yahoo.empty and df_coinex.empty:
        raise ValueError("هر دو منبع دیتا (Yahoo و CoinEx) خالی برگشتند — بررسی اتصال/نماد لازم است.")

    if df_yahoo.empty:
        # فقط CoinEx در دسترس است؛ بدون کالیبراسیون (تاریخچه کوتاه‌تر ولی معتبر) ادامه می‌دهیم.
        combined = df_coinex.copy()
        combined.attrs["calibration_ratio"] = None
        combined.attrs["yahoo_missing"] = True
        return combined

    if df_coinex.empty:
        # فقط Yahoo در دسترس است (بدون کالیبراسیون، چون منبع حقیقت Live نداریم).
        combined = df_yahoo.copy()
        combined.attrs["calibration_ratio"] = None
        combined.attrs["coinex_missing"] = True
        return combined

    ratio = compute_calibration_ratio(df_yahoo, df_coinex)
    _, overlap_end = find_overlap(df_yahoo, df_coinex)

    yahoo_part = df_yahoo.loc[df_yahoo.index < overlap_end]
    yahoo_calibrated = calibrate_yahoo_to_coinex(yahoo_part, ratio)

    coinex_part = df_coinex.loc[df_coinex.index >= overlap_end]

    combined = pd.concat([yahoo_calibrated, coinex_part]).sort_index()
    combined = combined[~combined.index.duplicated(keep="last")]
    combined.attrs["calibration_ratio"] = ratio
    return combined
