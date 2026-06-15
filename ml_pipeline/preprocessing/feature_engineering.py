"""Feature engineering pipeline for offline training."""

from __future__ import annotations

import pandas as pd


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create time-series features from OHLCV market data."""
    engineered = df.copy()
    engineered["return_1"] = engineered["close"].pct_change(1)
    engineered["return_5"] = engineered["close"].pct_change(5)
    engineered["sma_20"] = engineered["close"].rolling(20).mean()
    engineered["ema_20"] = engineered["close"].ewm(span=20, adjust=False).mean()
    engineered = engineered.dropna().reset_index(drop=True)
    return engineered
