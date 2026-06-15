"""Phase 2 ML feature/predictor/endpoint tests."""

from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_db
from app.main import app
from app.ml.feature_engineering import FEATURE_COLUMNS, compute_features
from app.ml.predictor import PredictionResult, predict_price
from app.models.financial_data import FinancialData
from app.models.model_log import ModelLog
from app.models.prediction import ModelType, Prediction


class _FakeScalarResult:
    def __init__(self, rows):
        self._rows = list(rows)

    def all(self):
        return list(self._rows)

    def first(self):
        return self._rows[0] if self._rows else None


class _FakeExecuteResult:
    def __init__(self, rows):
        self._rows = list(rows)

    def scalars(self):
        return _FakeScalarResult(self._rows)

    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else None


class _FakeSession:
    def __init__(self):
        self.financial_rows: list[FinancialData] = []
        self.predictions: list[Prediction] = []
        self.model_logs: list[ModelLog] = []

    def add(self, row):
        if isinstance(row, Prediction):
            self.predictions.append(row)

    async def execute(self, stmt):
        sql_text = str(stmt)
        params = stmt.compile().params

        if "FROM financial_data" in sql_text:
            ticker = str(params.get("ticker_1", "")).upper()
            rows = [row for row in self.financial_rows if row.ticker == ticker]
            rows.sort(key=lambda item: item.date)
            return _FakeExecuteResult(rows)

        if "FROM predictions" in sql_text:
            if "id_1" in params:
                needle = params["id_1"]
                rows = [row for row in self.predictions if row.id == needle]
                return _FakeExecuteResult(rows)

            rows = sorted(
                self.predictions,
                key=lambda item: item.created_at or date.today(),
                reverse=True,
            )[:50]
            return _FakeExecuteResult(rows)

        if "FROM model_logs" in sql_text:
            ticker = str(params.get("ticker_1", "")).upper()
            rows = [row for row in self.model_logs if row.ticker == ticker and row.is_active]
            rows.sort(key=lambda item: item.trained_at or date.min, reverse=True)
            return _FakeExecuteResult(rows[:1])

        return _FakeExecuteResult([])


def _build_market_df(rows: int = 60) -> pd.DataFrame:
    base = date(2026, 1, 1)
    index = np.arange(rows, dtype=np.float32)
    closes = 110.0 + (index * 0.35) + (np.sin(index / 3.0) * 2.5)
    volumes = 1_200_000 + (np.cos(index / 4.0) * 90_000)
    return pd.DataFrame(
        {
            "date": [base + timedelta(days=i) for i in range(rows)],
            "open": closes - 0.5,
            "high": closes + 1.5,
            "low": closes - 1.5,
            "close": closes,
            "volume": volumes,
        }
    )


def _seed_financial_rows(session: _FakeSession, ticker: str = "AAPL", rows: int = 60) -> None:
    frame = _build_market_df(rows)
    session.financial_rows = [
        FinancialData(
            id=uuid4(),
            ticker=ticker,
            date=row.date,
            open=float(row.open),
            high=float(row.high),
            low=float(row.low),
            close=float(row.close),
            volume=float(row.volume),
            source="synthetic",
        )
        for row in frame.itertuples(index=False)
    ]


def test_compute_features_output_columns():
    frame = _build_market_df(50)
    out = compute_features(frame)
    for col in FEATURE_COLUMNS:
        assert col in out.columns


@pytest.mark.asyncio
async def test_predict_ml_returns_result():
    session = _FakeSession()
    features = {
        "close": 123.4,
        "sma_5": 122.0,
        "sma_20": 118.0,
        "rsi_14": 56.0,
        "macd_signal": 1.2,
        "bb_width": 0.08,
        "daily_return": 0.01,
        "volume_zscore": 0.15,
    }
    result = await predict_price("AAPL", features, "ml", session)
    assert isinstance(result, PredictionResult)
    assert result.ticker == "AAPL"
    assert result.model_type == "ml"


@pytest.mark.asyncio
async def test_predict_dl_fallback(monkeypatch):
    monkeypatch.setenv("ENFORCE_REAL_MODELS", "false")
    session = _FakeSession()
    features = {
        "close": 100.0,
        "sma_5": 99.0,
        "sma_20": 97.0,
        "rsi_14": 52.0,
        "macd_signal": 0.8,
        "bb_width": 0.06,
        "daily_return": 0.005,
        "volume_zscore": -0.2,
    }
    result = await predict_price("AAPL", features, "dl", session)
    assert result.model_type == "ml_fallback"


@pytest.mark.asyncio
async def test_predict_ensemble_no_dl(monkeypatch):
    monkeypatch.setenv("ENFORCE_REAL_MODELS", "false")
    session = _FakeSession()
    features = {
        "close": 101.0,
        "sma_5": 100.0,
        "sma_20": 99.5,
        "rsi_14": 54.0,
        "macd_signal": 1.0,
        "bb_width": 0.05,
        "daily_return": 0.004,
        "volume_zscore": 0.1,
    }
    result = await predict_price("AAPL", features, "ensemble", session)
    assert isinstance(result.predicted_value, float)


def test_post_predict_endpoint_200():
    session = _FakeSession()
    _seed_financial_rows(session, ticker="AAPL", rows=65)

    async def _override_db():
        yield session

    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)
    try:
        response = client.post("/api/predict", json={"ticker": "AAPL", "model_type": "ml"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "predicted_value" in response.json()


def test_predict_history_endpoint():
    session = _FakeSession()
    session.predictions.append(
        Prediction(
            id=uuid4(),
            user_id=uuid4(),
            ticker="AAPL",
            model_type=ModelType.ML,
            predicted_value=123.45,
            confidence_score=0.87,
            features_used={"sma_5": 120.0},
        )
    )

    async def _override_db():
        yield session

    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)
    try:
        response = client.get("/api/predict/history")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert isinstance(response.json(), list)
