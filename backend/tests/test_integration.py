from __future__ import annotations

from datetime import date, timedelta
import math
from uuid import uuid4

import httpx
import pytest

import app.core.config as cfg
from app.api.deps import get_db
from app.main import app
from app.middleware.rate_limit import InMemoryRateLimiter
from app.models.financial_data import FinancialData
from app.models.prediction import Prediction


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

    async def execute(self, stmt):
        sql_text = str(stmt)
        params = stmt.compile().params

        if "FROM financial_data" in sql_text:
            ticker = str(params.get("ticker_1", "")).upper()
            rows = [row for row in self.financial_rows if row.ticker == ticker]
            rows.sort(key=lambda item: item.date)
            return _FakeExecuteResult(rows)

        if "FROM predictions" in sql_text:
            rows = sorted(
                self.predictions,
                key=lambda item: item.created_at or date.today(),
                reverse=True,
            )[:50]
            return _FakeExecuteResult(rows)

        if "FROM model_logs" in sql_text:
            return _FakeExecuteResult([])

        return _FakeExecuteResult([])

    def add(self, row):
        if isinstance(row, Prediction):
            self.predictions.append(row)


@pytest.fixture
def fake_session() -> _FakeSession:
    session = _FakeSession()
    base = date(2026, 1, 1)

    for i in range(80):
        close = 160.0 + (i * 0.2) + (math.sin(i / 3.0) * 1.8)
        session.financial_rows.append(
            FinancialData(
                id=uuid4(),
                ticker="AAPL",
                date=base + timedelta(days=i),
                open=close - 0.6,
                high=close + 1.3,
                low=close - 1.2,
                close=close,
                volume=1_500_000 + (i * 2_000),
                source="test",
            )
        )

    return session


@pytest.fixture
def override_db(fake_session: _FakeSession):
    async def _override_db():
        yield fake_session

    app.dependency_overrides[get_db] = _override_db
    try:
        yield fake_session
    finally:
        app.dependency_overrides.pop(get_db, None)


def _get_rate_limiter() -> InMemoryRateLimiter | None:
    stack = app.middleware_stack
    for _ in range(30):
        if isinstance(stack, InMemoryRateLimiter):
            return stack
        stack = getattr(stack, "app", None)
        if stack is None:
            break
    return None


@pytest.fixture(autouse=True)
def _clear_rate_limit_windows():
    limiter = _get_rate_limiter()
    if limiter is not None:
        limiter._windows.clear()
    yield
    limiter = _get_rate_limiter()
    if limiter is not None:
        limiter._windows.clear()


@pytest.mark.asyncio
async def test_health_check():
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/health")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_predict_then_history(override_db):
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        r1 = await ac.post("/api/predict", json={"ticker": "AAPL", "model_type": "ml"})
        assert r1.status_code == 200
        r2 = await ac.get("/api/predict/history")
        assert r2.status_code == 200
        assert isinstance(r2.json(), list)


@pytest.mark.asyncio
async def test_forecast_shape(override_db):
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/api/forecast", json={"ticker": "AAPL", "horizon_days": 7})
    assert r.status_code == 200
    assert len(r.json()["forecast"]) == 7


@pytest.mark.asyncio
async def test_rate_limit_429(monkeypatch):
    monkeypatch.setattr(cfg.settings, "RATE_LIMIT_PER_MINUTE", 2)
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        for _ in range(2):
            ok = await ac.get("/health")
            assert ok.status_code == 200
        r = await ac.get("/health")
    assert r.status_code == 429
