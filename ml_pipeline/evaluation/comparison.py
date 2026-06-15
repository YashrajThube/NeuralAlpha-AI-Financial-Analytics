"""Champion-challenger comparison and rollback utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

import pandas as pd

from ml_pipeline.evaluation.backtester import BacktestResult


@dataclass(slots=True)
class ModelRecord:
    """Versioned model performance record."""

    model_version: str
    dataset_version: str
    metrics: dict[str, float]
    artifact_path: str


class ChampionChallenger:
    """Compare models and pick the best one automatically."""

    def __init__(self, metric_key: str = "lstm_vs_naive_mae_improvement") -> None:
        self.metric_key = metric_key

    def select_champion(self, records: list[ModelRecord]) -> ModelRecord:
        if not records:
            raise ValueError("No candidate records provided.")
        return max(records, key=lambda record: float(record.metrics.get(self.metric_key, float("-inf"))))

    def compare_results(self, results: list[BacktestResult]) -> pd.DataFrame:
        rows = []
        for result in results:
            rows.append(
                {
                    "model_version": result.model_version,
                    "dataset_version": result.dataset_version,
                    **result.metrics,
                    **result.baseline_metrics,
                }
            )
        return pd.DataFrame(rows)


class RollbackManager:
    """Auto rollback helper that stores and restores champion metadata."""

    def __init__(self, registry_path: str) -> None:
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

    def write_champion(self, record: ModelRecord) -> None:
        payload = {
            "model_version": record.model_version,
            "dataset_version": record.dataset_version,
            "artifact_path": record.artifact_path,
            "metrics": record.metrics,
        }
        self.registry_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load_champion(self) -> ModelRecord:
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Registry not found: {self.registry_path}")
        payload = json.loads(self.registry_path.read_text(encoding="utf-8"))
        return ModelRecord(
            model_version=str(payload["model_version"]),
            dataset_version=str(payload["dataset_version"]),
            artifact_path=str(payload["artifact_path"]),
            metrics=dict(payload["metrics"]),
        )

    def should_rollback(self, current: ModelRecord, previous: ModelRecord, threshold: float = 0.0) -> bool:
        current_score = float(current.metrics.get("lstm_vs_naive_mae_improvement", 0.0))
        previous_score = float(previous.metrics.get("lstm_vs_naive_mae_improvement", 0.0))
        return (current_score + threshold) < previous_score
