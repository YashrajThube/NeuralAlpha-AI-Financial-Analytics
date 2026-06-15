"""Phase 3 DL forecast endpoint tests with graceful fallback behavior."""

from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

import numpy as np
from fastapi.testclient import TestClient

from app.api.deps import get_db
from app.main import app
from app.models.financial_data import FinancialData


class _FakeScalarResult:
    def __init__(self, rows):
        self._rows = list(rows)

    def all(self):
        return list(self._rows)


class _FakeExecuteResult:
    def __init__(self, rows):
        self._rows = list(rows)

    def scalars(self):
        return _FakeScalarResult(self._rows)


class _FakeSession:
    def __init__(self):
        self.financial_rows: list[FinancialData] = []

    async def execute(self, stmt):
        sql_text = str(stmt)
        params = stmt.compile().params
        if "FROM financial_data" in sql_text:
            ticker = str(params.get("ticker_1", "")).upper()
            rows = [row for row in self.financial_rows if row.ticker == ticker]
            rows.sort(key=lambda item: item.date)
            return _FakeExecuteResult(rows)
        return _FakeExecuteResult([])


def _seed_rows(session: _FakeSession, ticker: str = "AAPL", rows: int = 70) -> None:
    start = date(2026, 1, 1)
    idx = np.arange(rows, dtype=np.float32)
    closes = 120.0 + (idx * 0.25) + (np.sin(idx / 5.0) * 1.8)
    volumes = 1_300_000 + (np.cos(idx / 6.0) * 75_000)
    session.financial_rows = [
        FinancialData(
            id=uuid4(),
            ticker=ticker,
            date=start + timedelta(days=i),
            open=float(closes[i] - 0.8),
            high=float(closes[i] + 1.2),
            low=float(closes[i] - 1.3),
            close=float(closes[i]),
            volume=float(volumes[i]),
            source="synthetic",
        )
        for i in range(rows)
    ]


def _client_with_session(session: _FakeSession) -> TestClient:
    async def _override_db():
        yield session

    app.dependency_overrides[get_db] = _override_db
    return TestClient(app)


def test_forecast_endpoint_shape(monkeypatch):
    monkeypatch.setenv("ENFORCE_REAL_MODELS", "false")
    session = _FakeSession()
    _seed_rows(session)
    client = _client_with_session(session)
    try:
        response = client.post("/api/forecast", json={"ticker": "AAPL", "horizon_days": 5})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert "forecast" in body
    assert len(body["forecast"]) == 5


def test_forecast_fallback_no_dl(monkeypatch):
    monkeypatch.setenv("ENFORCE_REAL_MODELS", "false")
    session = _FakeSession()
    _seed_rows(session)
    client = _client_with_session(session)
    try:
        response = client.post("/api/forecast", json={"ticker": "AAPL", "horizon_days": 7})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(response.json()["forecast"]) == 7


def test_each_forecast_item_has_required_keys(monkeypatch):
    monkeypatch.setenv("ENFORCE_REAL_MODELS", "false")
    session = _FakeSession()
    _seed_rows(session)
    client = _client_with_session(session)
    try:
        response = client.post("/api/forecast", json={"ticker": "AAPL", "horizon_days": 5})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    for item in response.json()["forecast"]:
        assert "day" in item
        assert "predicted_value" in item
        assert "confidence" in item


def test_horizon_validation_rejects_zero(monkeypatch):
    monkeypatch.setenv("ENFORCE_REAL_MODELS", "false")
    session = _FakeSession()
    _seed_rows(session)
    client = _client_with_session(session)
    try:
        response = client.post("/api/forecast", json={"ticker": "AAPL", "horizon_days": 0})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_horizon_validation_rejects_31(monkeypatch):
    monkeypatch.setenv("ENFORCE_REAL_MODELS", "false")
    session = _FakeSession()
    _seed_rows(session)
    client = _client_with_session(session)
    try:
        response = client.post("/api/forecast", json={"ticker": "AAPL", "horizon_days": 31})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
