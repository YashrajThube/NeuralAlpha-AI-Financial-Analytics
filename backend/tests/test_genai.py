from __future__ import annotations

from datetime import date
from uuid import uuid4

import anthropic
from fastapi.testclient import TestClient

from app.deps import get_db, get_genai_service
from app.main import app
from app.models.financial_data import FinancialData
from app.models.prediction import ModelType, Prediction


class MockGenAIService:
    def chat(self, user_message, ticker, conversation_history, db):
        _ = user_message, conversation_history, db
        return "Mock reply about " + ticker

    def generate_insight(self, ticker, prediction, financial_data):
        _ = ticker, prediction, financial_data
        return "Mock insight paragraph 1. Mock paragraph 2. Mock paragraph 3."


def get_mock_genai():
    return MockGenAIService()


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


class _FakeDB:
    def __init__(self):
        self.fin = FinancialData(
            id=uuid4(),
            ticker="AAPL",
            date=date(2026, 1, 1),
            open=100.0,
            high=103.0,
            low=99.5,
            close=102.0,
            volume=1000000.0,
            source="synthetic",
        )
        self.pred = Prediction(
            id=uuid4(),
            user_id=uuid4(),
            ticker="AAPL",
            model_type=ModelType.ML,
            predicted_value=104.5,
            confidence_score=0.82,
            features_used={"model_version": "default-v1"},
        )

    async def execute(self, stmt):
        sql = str(stmt)
        params = stmt.compile().params
        ticker = str(params.get("ticker_1", "")).upper()
        if "FROM financial_data" in sql and ticker == "AAPL":
            return _FakeExecuteResult([self.fin])
        if "FROM predictions" in sql and ticker == "AAPL":
            return _FakeExecuteResult([self.pred])
        return _FakeExecuteResult([])


def test_chat_returns_reply():
    app.dependency_overrides[get_genai_service] = get_mock_genai

    async def _db_override():
        yield _FakeDB()

    app.dependency_overrides[get_db] = _db_override

    client = TestClient(app)
    r = client.post("/api/chat", json={"message": "What is AAPL?", "ticker": "AAPL", "conversation_history": []})
    assert r.status_code == 200
    assert "reply" in r.json()
    app.dependency_overrides.clear()


def test_insight_returns_insight():
    app.dependency_overrides[get_genai_service] = get_mock_genai

    async def _db_override():
        yield _FakeDB()

    app.dependency_overrides[get_db] = _db_override

    client = TestClient(app)
    r = client.post("/api/ai-insight", json={"ticker": "AAPL"})
    assert r.status_code == 200
    assert "insight" in r.json()
    app.dependency_overrides.clear()


def test_chat_503_on_api_error():
    class ErrorGenAI:
        def chat(self, *a, **kw):
            _ = a, kw
            raise anthropic.APIError("fail", request=None, body=None)

    app.dependency_overrides[get_genai_service] = lambda: ErrorGenAI()

    async def _db_override():
        yield _FakeDB()

    app.dependency_overrides[get_db] = _db_override

    client = TestClient(app)
    r = client.post("/api/chat", json={"message": "test", "ticker": "AAPL", "conversation_history": []})
    assert r.status_code == 503
    app.dependency_overrides.clear()
