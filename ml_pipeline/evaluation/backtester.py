"""Backtesting engine for ML and DL forecasting models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model as keras_load_model  # type: ignore[import-not-found]

from ml_pipeline.evaluation.metrics import accuracy_score, direction_accuracy, mae, rmse, roc_auc_score
from ml_pipeline.preprocessing.feature_engineering import create_features


@dataclass(slots=True)
class BacktestArtifacts:
    """Loaded backtest artifacts."""

    xgb_model: Any
    lstm_model: Any
    scaler: Any
    model_version: str
    dataset_version: str
    window_size: int


@dataclass(slots=True)
class BacktestResult:
    """Evaluation output with metrics and prediction history."""

    model_version: str
    dataset_version: str
    metrics: dict[str, float]
    predictions: pd.DataFrame
    baseline_metrics: dict[str, float]


class EvaluationPipeline:
    """Evaluate model performance on historical data using walk-forward backtesting."""

    def __init__(
        self,
        xgb_model_path: str,
        lstm_model_path: str,
        scaler_path: str,
        model_version: str,
        dataset_version: str,
        window_size: int = 10,
        evaluation_db_path: str | None = None,
    ) -> None:
        self.xgb_model_path = Path(xgb_model_path)
        self.lstm_model_path = Path(lstm_model_path)
        self.scaler_path = Path(scaler_path)
        self.model_version = model_version
        self.dataset_version = dataset_version
        self.window_size = window_size
        self.evaluation_db_path = Path(evaluation_db_path) if evaluation_db_path else None

    def load_artifacts(self) -> BacktestArtifacts:
        """Load persisted model artifacts."""
        if not self.xgb_model_path.exists():
            raise FileNotFoundError(f"Missing XGBoost model: {self.xgb_model_path}")
        if not self.lstm_model_path.exists():
            raise FileNotFoundError(f"Missing LSTM model: {self.lstm_model_path}")
        if not self.scaler_path.exists():
            raise FileNotFoundError(f"Missing scaler: {self.scaler_path}")

        xgb_model = joblib.load(self.xgb_model_path)
        lstm_model = keras_load_model(self.lstm_model_path)
        scaler_payload = joblib.load(self.scaler_path)
        scaler = scaler_payload["scaler"] if isinstance(scaler_payload, dict) else scaler_payload
        window_size = int(scaler_payload.get("window_size", self.window_size)) if isinstance(scaler_payload, dict) else self.window_size
        return BacktestArtifacts(
            xgb_model=xgb_model,
            lstm_model=lstm_model,
            scaler=scaler,
            model_version=self.model_version,
            dataset_version=self.dataset_version,
            window_size=window_size,
        )

    @staticmethod
    def _prepare_frame(df: pd.DataFrame) -> pd.DataFrame:
        """Prepare historical frame and create engineered features."""
        if "close" not in df.columns:
            raise ValueError("Input dataframe must contain a `close` column.")
        cleaned = df.copy()
        cleaned["close"] = pd.to_numeric(cleaned["close"], errors="coerce")
        cleaned = cleaned.replace([np.inf, -np.inf], np.nan).dropna(subset=["close"]).reset_index(drop=True)
        return create_features(cleaned)

    def _walk_forward_rows(self, df: pd.DataFrame, artifacts: BacktestArtifacts) -> pd.DataFrame:
        """Generate predictions for each walk-forward step."""
        rows: list[dict[str, float]] = []
        close = df["close"].to_numpy(dtype=np.float32)
        if close.size <= max(self.window_size + 20, 50):
            raise ValueError("Not enough historical rows for backtesting.")

        for idx in range(max(self.window_size + 20, 20), len(df) - 1):
            historical = df.iloc[: idx + 1].copy()
            target_close = float(df.iloc[idx + 1]["close"])
            current_close = float(df.iloc[idx]["close"])

            features = create_features(historical)
            latest = features.iloc[-1]
            feature_vector = np.asarray(
                [[float(latest["return_1"]), float(latest["return_5"]), float(latest["sma_20"]), float(latest["ema_20"])]],
                dtype=np.float32,
            )

            if not hasattr(artifacts.xgb_model, "predict_proba"):
                raise RuntimeError("XGBoost artifact must support predict_proba for evaluation.")
            proba = artifacts.xgb_model.predict_proba(feature_vector)
            prob_up = float(proba[0, 1]) if proba.ndim == 2 and proba.shape[1] > 1 else 0.5
            ml_class_pred = 1 if prob_up >= 0.5 else 0
            ml_pred = current_close * (1.0 + ((2.0 * prob_up) - 1.0) * abs(float(latest["return_1"])))

            seq = close[max(0, idx + 1 - artifacts.window_size) : idx + 1]
            if seq.size < artifacts.window_size:
                continue
            seq_scaled = artifacts.scaler.transform(seq.reshape(-1, 1)).astype(np.float32, copy=False)
            lstm_input = seq_scaled.reshape(1, artifacts.window_size, 1)
            lstm_scaled = artifacts.lstm_model.predict(lstm_input, verbose=0)
            lstm_pred = float(artifacts.scaler.inverse_transform(np.asarray(lstm_scaled).reshape(1, 1))[0, 0])

            naive_pred = float(seq[-1])
            final_pred = 0.4 * ml_pred + 0.6 * lstm_pred

            rows.append(
                {
                    "timestamp": float(idx + 1),
                    "actual": target_close,
                    "ml_pred": float(ml_pred),
                    "ml_prob_up": prob_up,
                    "ml_class_pred": float(ml_class_pred),
                    "lstm_pred": float(lstm_pred),
                    "naive_pred": naive_pred,
                    "final_pred": float(final_pred),
                    "direction_true": float(1 if target_close > current_close else 0),
                    "direction_pred_ml": float(1 if prob_up >= 0.5 else 0),
                    "direction_pred_lstm": float(1 if lstm_pred > current_close else 0),
                    "direction_pred_final": float(1 if final_pred > current_close else 0),
                    "direction_pred_naive": float(1 if naive_pred > current_close else 0),
                }
            )

        if not rows:
            raise ValueError("Backtest produced no rows. Check input data and window size.")
        return pd.DataFrame(rows)

    def evaluate(self, df: pd.DataFrame) -> BacktestResult:
        """Run walk-forward backtesting and compute metrics."""
        artifacts = self.load_artifacts()
        prepared = self._prepare_frame(df)
        results = self._walk_forward_rows(prepared, artifacts)

        y_true = results["actual"].to_numpy(dtype=np.float64)
        ml_scores = results["ml_prob_up"].to_numpy(dtype=np.float64)
        ml_binary = results["direction_pred_ml"].to_numpy(dtype=np.float64)
        lstm_pred = results["lstm_pred"].to_numpy(dtype=np.float64)
        naive_pred = results["naive_pred"].to_numpy(dtype=np.float64)
        final_pred = results["final_pred"].to_numpy(dtype=np.float64)
        direction_true = results["direction_true"].to_numpy(dtype=np.float64)
        direction_final = results["direction_pred_final"].to_numpy(dtype=np.float64)
        direction_lstm = results["direction_pred_lstm"].to_numpy(dtype=np.float64)
        direction_naive = results["direction_pred_naive"].to_numpy(dtype=np.float64)

        ml_metrics = {
            "accuracy": accuracy_score(direction_true, ml_binary),
            "roc_auc": roc_auc_score(direction_true, ml_scores),
        }
        dl_metrics = {
            "mae": mae(y_true, lstm_pred),
            "rmse": rmse(y_true, lstm_pred),
            "direction_accuracy": direction_accuracy(y_true, lstm_pred),
        }
        baseline_metrics = {
            "naive_mae": mae(y_true, naive_pred),
            "naive_rmse": rmse(y_true, naive_pred),
            "naive_direction_accuracy": accuracy_score(direction_true, direction_naive),
        }
        comparison = {
            "lstm_vs_naive_mae_improvement": baseline_metrics["naive_mae"] - dl_metrics["mae"],
            "lstm_vs_naive_rmse_improvement": baseline_metrics["naive_rmse"] - dl_metrics["rmse"],
            "ml_vs_dl_direction_gap": ml_metrics["accuracy"] - dl_metrics["direction_accuracy"],
            "final_direction_accuracy": accuracy_score(direction_true, direction_final),
            "lstm_direction_accuracy": accuracy_score(direction_true, direction_lstm),
        }
        metrics = {**ml_metrics, **dl_metrics, **comparison}
        return BacktestResult(
            model_version=artifacts.model_version,
            dataset_version=artifacts.dataset_version,
            metrics=metrics,
            predictions=results,
            baseline_metrics=baseline_metrics,
        )
