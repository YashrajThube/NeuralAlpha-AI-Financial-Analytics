"""
Train XGBoost binary classifier: predict next-day price direction.
Produces xgb.joblib compatible with predictor.py which calls
predict() for class label and predict_proba() for prob_up.
"""

from __future__ import annotations
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml_pipeline.preprocessing.feature_engineering import create_features

MODEL_OUTPUT = Path("ml_pipeline/models/xgb.joblib")
DATA_PATH = Path("ml_pipeline/data/raw/stock_market_data.csv")


def train_xgboost_classifier(data_path: Path, model_output: Path) -> str:
    df = pd.read_csv(data_path)
    features = create_features(df)

    X = features[["return_1", "return_5", "sma_20", "ema_20"]].to_numpy(dtype=np.float32)
    # Binary label: 1 if next close > current close else 0
    close = features["close"].to_numpy()
    y = (np.diff(close, append=close[-1]) > 0).astype(int)
    # Remove last row (no next close known)
    X, y = X[:-1], y[:-1]

    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    model = XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=42,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    acc = float(np.mean(model.predict(X_test) == y_test))
    print(f"XGBoost test accuracy: {acc:.4f}")

    model_output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_output)
    print(f"Saved XGBoost model to {model_output}")
    return str(model_output)


if __name__ == "__main__":
    train_xgboost_classifier(DATA_PATH, MODEL_OUTPUT)
