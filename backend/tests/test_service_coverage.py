from __future__ import annotations

import json
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from app.services.monitoring_service import MonitoringService
from app.services.portfolio_service import PortfolioService
from app.services.sentiment_service import SentimentService


class _FakeScalarResult:
    def __init__(self, rows):
        self._rows = list(rows)

    def all(self):
        return list(self._rows)


class _FakeExecuteResult:
    def __init__(self, rows=None, scalar_value=None):
        self._rows = list(rows or [])
        self._scalar_value = scalar_value

    def scalars(self):
        return _FakeScalarResult(self._rows)

    def scalar_one(self):
        return self._scalar_value


class _FakeMonitoringDB:
    def __init__(self):
        now = datetime.utcnow()
        self.logs = [
            SimpleNamespace(
                action='prediction.request',
                status='success',
                message=json.dumps({'latency_ms': 110.0}),
                timestamp=now - timedelta(minutes=50),
            ),
            SimpleNamespace(
                action='forecast.request',
                status='error',
                message=json.dumps({'latency_ms': 1800.0}),
                timestamp=now - timedelta(minutes=30),
            ),
            SimpleNamespace(
                action='chat.request',
                status='success',
                message=json.dumps({'latency_ms': 900.0, 'fallback_used': True}),
                timestamp=now - timedelta(minutes=10),
            ),
            SimpleNamespace(
                action='chat.request',
                status='success',
                message=json.dumps({'latency_ms': 950.0, 'fallback_used': False}),
                timestamp=now - timedelta(minutes=5),
            ),
        ]

    async def execute(self, stmt):
        sql = str(stmt)
        if 'count(predictions.id)' in sql:
            return _FakeExecuteResult(scalar_value=12)
        if 'avg(predictions.confidence)' in sql:
            return _FakeExecuteResult(scalar_value=0.74)
        if 'FROM logs' in sql:
            return _FakeExecuteResult(rows=self.logs)
        return _FakeExecuteResult(rows=[])


class _FakePortfolioDB:
    def __init__(self):
        self.rows = [
            SimpleNamespace(symbol='AAPL', quantity=10.0, avg_price=150.0, current_price=175.0),
            SimpleNamespace(symbol='MSFT', quantity=5.0, avg_price=300.0, current_price=320.0),
        ]

    async def execute(self, stmt):
        _ = stmt
        return _FakeExecuteResult(rows=self.rows)


class _FakeSentimentDB:
    def __init__(self):
        self.added = []

    async def execute(self, stmt):
        _ = stmt
        return _FakeExecuteResult(rows=[])

    def add(self, row):
        self.added.append(row)

    async def flush(self):
        return None

    async def refresh(self, row):
        return row


@pytest.mark.asyncio
async def test_monitoring_service_metrics_and_alerts(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, 'monitoring_latency_alert_ms', 500.0)
    monkeypatch.setattr(settings, 'monitoring_error_rate_alert', 0.1)
    monkeypatch.setattr(settings, 'monitoring_fallback_alert', 0.2)

    data = await MonitoringService.get_metrics(_FakeMonitoringDB())

    assert data.total_predictions_24h == 12
    assert data.avg_confidence_24h == 0.74
    assert data.error_rate_24h > 0
    assert data.p95_latency_ms >= 900
    assert len(data.alerts) >= 2


@pytest.mark.asyncio
async def test_sentiment_service_generates_and_persists(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, 'cache_enabled', False)

    result = await SentimentService.analyze('aapl', _FakeSentimentDB())

    assert result.symbol == 'AAPL'
    assert result.label in {'Positive', 'Negative', 'Neutral'}


@pytest.mark.asyncio
async def test_portfolio_summary_computes_weights():
    user = SimpleNamespace(id=1)
    summary = await PortfolioService.summary(user, _FakePortfolioDB())

    assert summary['positions'] == 2
    assert summary['total_market_value'] > 0
    assert any(item['symbol'] == 'AAPL' for item in summary['holdings'])
    assert round(sum(item['weight_pct'] for item in summary['holdings']), 3) == 100.0
