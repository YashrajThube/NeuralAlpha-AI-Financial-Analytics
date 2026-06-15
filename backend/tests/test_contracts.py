from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.middleware.contract_middleware import ObservabilityValidationMiddleware
from app.middleware.rate_limit import InMemoryRateLimiter


def _build_rate_limited_app(limit: int) -> FastAPI:
    local = FastAPI()

    @local.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    settings.RATE_LIMIT_PER_MINUTE = limit
    local.add_middleware(InMemoryRateLimiter)
    return local


def test_rate_limit_passes_under_limit():
    local_app = _build_rate_limited_app(limit=60)
    client = TestClient(local_app)
    statuses = [client.get("/health").status_code for _ in range(5)]
    assert statuses == [200, 200, 200, 200, 200]


def test_rate_limit_blocks_over_limit(monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_MINUTE", 2)
    local_app = _build_rate_limited_app(limit=2)
    client = TestClient(local_app)
    first = client.get("/health")
    second = client.get("/health")
    third = client.get("/health")
    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429


def test_contract_middleware_not_mounted_when_strict_false():
    settings.STRICT_API_VALIDATION = False
    classes = [m.cls for m in app.user_middleware]
    assert ObservabilityValidationMiddleware not in classes


def test_contract_schema_predict_valid():
    from app.schemas.contracts import PredictionContractResponse

    obj = PredictionContractResponse(
        predicted_value=150.0,
        confidence_score=0.85,
        model_type="ml",
        model_version="v1",
        ticker="AAPL",
    )
    assert obj.predicted_value == 150.0
