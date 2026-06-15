"""Reporting utilities for backtest summaries and plots."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from ml_pipeline.evaluation.backtester import BacktestResult


class EvaluationReporter:
    """Generate tables and simple plots for evaluation results."""

    @staticmethod
    def summary_table(result: BacktestResult) -> pd.DataFrame:
        rows = []
        for key, value in result.metrics.items():
            rows.append({"metric": key, "value": value})
        for key, value in result.baseline_metrics.items():
            rows.append({"metric": key, "value": value})
        rows.append({"metric": "model_version", "value": result.model_version})
        rows.append({"metric": "dataset_version", "value": result.dataset_version})
        return pd.DataFrame(rows)

    @staticmethod
    def plot_predictions(result: BacktestResult) -> None:
        df = result.predictions
        plt.figure(figsize=(10, 4))
        plt.plot(df["actual"].to_numpy(), label="Actual", linewidth=1.5)
        plt.plot(df["lstm_pred"].to_numpy(), label="LSTM", linewidth=1.2)
        plt.plot(df["naive_pred"].to_numpy(), label="Naive", linewidth=1.2, linestyle="--")
        plt.plot(df["final_pred"].to_numpy(), label="Final", linewidth=1.2)
        plt.title("Model vs Baseline Predictions")
        plt.xlabel("Backtest Step")
        plt.ylabel("Price")
        plt.legend()
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_metric_bars(result: BacktestResult) -> None:
        metrics = result.metrics
        baseline = result.baseline_metrics
        labels = ["LSTM MAE", "Naive MAE", "LSTM RMSE", "Naive RMSE"]
        values = [metrics.get("mae", 0.0), baseline.get("naive_mae", 0.0), metrics.get("rmse", 0.0), baseline.get("naive_rmse", 0.0)]
        plt.figure(figsize=(8, 4))
        plt.bar(labels, values)
        plt.title("Error Comparison")
        plt.xticks(rotation=20)
        plt.tight_layout()
        plt.show()
