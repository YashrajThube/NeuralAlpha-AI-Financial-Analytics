"""High-level evaluation pipeline entrypoint."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3

import pandas as pd

from ml_pipeline.evaluation.backtester import BacktestResult, EvaluationPipeline
from ml_pipeline.evaluation.comparison import ChampionChallenger, ModelRecord, RollbackManager
from ml_pipeline.evaluation.reporting import EvaluationReporter


@dataclass(slots=True)
class EvaluationRunConfig:
    """Configuration for a full evaluation run."""

    xgb_model_path: str
    lstm_model_path: str
    scaler_path: str
    model_version: str
    dataset_version: str
    window_size: int = 10
    sqlite_path: str = "ml_pipeline/evaluation/evaluation.db"
    registry_path: str = "ml_pipeline/models/champion.json"


class EvaluationOrchestrator:
    """Runs backtests, stores metrics, compares models, and handles rollback."""

    def __init__(self, config: EvaluationRunConfig) -> None:
        self.config = config
        self.backtester = EvaluationPipeline(
            xgb_model_path=config.xgb_model_path,
            lstm_model_path=config.lstm_model_path,
            scaler_path=config.scaler_path,
            model_version=config.model_version,
            dataset_version=config.dataset_version,
            window_size=config.window_size,
            evaluation_db_path=config.sqlite_path,
        )
        self.reporter = EvaluationReporter()
        self.challenger = ChampionChallenger()
        self.rollback = RollbackManager(config.registry_path)

    def _persist(self, result: BacktestResult) -> None:
        path = Path(self.config.sqlite_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path) as conn:
            result.predictions.to_sql("backtest_predictions", conn, if_exists="append", index=False)
            pd.DataFrame(
                [
                    {
                        "model_version": result.model_version,
                        "dataset_version": result.dataset_version,
                        **result.metrics,
                        **result.baseline_metrics,
                    }
                ]
            ).to_sql("backtest_metrics", conn, if_exists="append", index=False)

    def run(self, df: pd.DataFrame) -> dict[str, object]:
        result = self.backtester.evaluate(df)
        self._persist(result)
        self.rollback.write_champion(
            ModelRecord(
                model_version=result.model_version,
                dataset_version=result.dataset_version,
                metrics=result.metrics,
                artifact_path=self.config.lstm_model_path,
            )
        )
        return {
            "summary": self.reporter.summary_table(result),
            "result": result,
        }

    def compare_and_choose(self, records: list[ModelRecord]) -> ModelRecord:
        return self.challenger.select_champion(records)
