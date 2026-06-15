"""Model evaluation metrics."""

from __future__ import annotations

import numpy as np


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate root mean squared error."""
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate mean absolute percentage error."""
    epsilon = 1e-8
    return float(np.mean(np.abs((y_true - y_pred) / (y_true + epsilon))) * 100)
