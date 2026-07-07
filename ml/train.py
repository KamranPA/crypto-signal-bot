# مسیر فایل: ml/train.py
"""آموزش مدل LightGBM اختصاصی هر ارز — walk-forward split، بدون shuffle رندوم."""
from __future__ import annotations
from pathlib import Path
import json
from datetime import datetime, timezone

import pandas as pd
import lightgbm as lgb
from sklearn.metrics import precision_recall_curve, roc_auc_score

from ml.features import FEATURE_COLUMNS

MODELS_DIR = Path(__file__).resolve().parent / "models"


def walk_forward_split(df: pd.DataFrame, train_ratio: float = 0.7):
    df = df.sort_values("timestamp")
    split_idx = int(len(df) * train_ratio)
    return df.iloc[:split_idx], df.iloc[split_idx:]


def train_model(labeled_df: pd.DataFrame, symbol: str, lgb_params: dict | None = None) -> dict:
    if lgb_params is None:
        lgb_params = {
            "objective": "binary",
            "metric": "auc",
            "num_leaves": 15,
            "learning_rate": 0.05,
            "n_estimators": 200,
            "min_child_samples": 20,
            "verbose": -1,
        }

    train_df, test_df = walk_forward_split(labeled_df)

    X_train, y_train = train_df[FEATURE_COLUMNS], train_df["label"]
    X_test, y_test = test_df[FEATURE_COLUMNS], test_df["label"]

    model = lgb.LGBMClassifier(**lgb_params)
    model.fit(X_train, y_train)

    proba_test = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, proba_test) if y_test.nunique() > 1 else float("nan")
    precision, recall, thresholds = precision_recall_curve(y_test, proba_test)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    version = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    model_path = MODELS_DIR / f"{symbol}_{version}.txt"
    model.booster_.save_model(str(model_path))

    metrics = {
        "auc": auc,
        "n_train": len(train_df),
        "n_test": len(test_df),
        "trained_at": version,
        "precision_recall_curve": {
            "precision": precision.tolist(),
            "recall": recall.tolist(),
            "thresholds": thresholds.tolist(),
        },
    }
    metrics_path = MODELS_DIR / f"{symbol}_{version}_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    return {"model": model, "model_path": model_path, "metrics": metrics, "version": version}
