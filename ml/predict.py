# مسیر فایل: ml/predict.py
"""بارگذاری آخرین مدل هر ارز و اعمال آستانه‌ی تأیید در job ساعتی."""
from __future__ import annotations
from pathlib import Path
import lightgbm as lgb
import pandas as pd

from ml.features import FEATURE_COLUMNS, extract_feature_row

MODELS_DIR = Path(__file__).resolve().parent / "models"


def load_latest_model(symbol: str) -> lgb.Booster | None:
    candidates = sorted(MODELS_DIR.glob(f"{symbol}_*.txt"))
    if not candidates:
        return None
    return lgb.Booster(model_file=str(candidates[-1]))


def predict_confidence(model: lgb.Booster, df_with_indicators: pd.DataFrame, idx: int) -> float:
    features = extract_feature_row(df_with_indicators, idx)
    row_df = pd.DataFrame([features])[FEATURE_COLUMNS]
    return float(model.predict(row_df)[0])


def is_signal_confirmed(model: lgb.Booster | None, df_with_indicators: pd.DataFrame,
                         idx: int, threshold: float) -> tuple[bool, float]:
    if model is None:
        return True, 1.0
    confidence = predict_confidence(model, df_with_indicators, idx)
    return confidence >= threshold, confidence
