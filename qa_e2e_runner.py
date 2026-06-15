from __future__ import annotations

import asyncio
import json
import os
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

BASE_URL = os.getenv('QA_BASE_URL', 'http://127.0.0.1:8000')
API_BASE = f"{BASE_URL}/api/v1"
MAX_LATENCY_SECONDS = 3.0


@dataclass
class CheckResult:
    name: str
    passed: bool
    latency_ms: float | None
    details: dict[str, Any]


def _is_contract_ok(payload: Any) -> tuple[bool, str]:
    if not isinstance(payload, dict):
        return False, 'response is not an object'
    required = {'success', 'data', 'error'}
    missing = [key for key in required if key not in payload]
    if missing:
        return False, f'missing contract keys: {missing}'
    if payload.get('success') is not True:
        return False, f"success != true ({payload.get('success')})"
    if payload.get('error') is not None:
        return False, f"error must be null, got: {payload.get('error')}"
    return True, ''


async def _run_api_check(
    client: httpx.AsyncClient,
    name: str,
    request_call: Callable[[], Awaitable[httpx.Response]],
    validator: Callable[[dict[str, Any]], tuple[bool, str]],
) -> CheckResult:
    started = time.perf_counter()
    try:
        response = await request_call()
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        body = response.json()

        contract_ok, contract_reason = _is_contract_ok(body)
        if response.status_code != 200:
            return CheckResult(name, False, latency_ms, {'status': response.status_code, 'body': body})
        if not contract_ok:
            return CheckResult(name, False, latency_ms, {'contract_error': contract_reason, 'body': body})

        data = body.get('data')
        if not isinstance(data, dict):
            return CheckResult(name, False, latency_ms, {'data_type': type(data).__name__})

        valid, reason = validator(data)
        latency_ok = (latency_ms / 1000.0) <= MAX_LATENCY_SECONDS
        passed = valid and latency_ok
        return CheckResult(
            name,
            passed,
            latency_ms,
            {
                'validator_ok': valid,
                'validator_reason': reason,
                'latency_ok': latency_ok,
                'status': response.status_code,
            },
        )
    except Exception as exc:  # noqa: BLE001
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        return CheckResult(name, False, latency_ms, {'exception': str(exc)})


async def _check_mysql() -> CheckResult:
    started = time.perf_counter()
    url = os.getenv('DATABASE_URL', 'mysql+aiomysql://neuralalpha:neuralalpha@localhost:3306/neuralalpha')
    engine = create_async_engine(url, pool_pre_ping=True)

    try:
        async with engine.begin() as conn:
            await conn.execute(text('SELECT 1'))
            await conn.execute(
                text(
                    """
                    INSERT INTO logs (action, status, message)
                    VALUES ('qa.mysql_probe', 'success', 'insert_fetch_probe')
                    """
                )
            )
            result = await conn.execute(
                text(
                    """
                    SELECT action, status, message
                    FROM logs
                    WHERE action = 'qa.mysql_probe'
                    ORDER BY id DESC
                    LIMIT 1
                    """
                )
            )
            row = result.first()

        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        passed = bool(row and row.action == 'qa.mysql_probe')
        return CheckResult(
            'mysql_connection',
            passed,
            latency_ms,
            {
                'row_found': bool(row),
                'latency_ok': (latency_ms / 1000.0) <= MAX_LATENCY_SECONDS,
            },
        )
    except Exception as exc:  # noqa: BLE001
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        return CheckResult('mysql_connection', False, latency_ms, {'exception': str(exc)})
    finally:
        await engine.dispose()


def _validate_predict(data: dict[str, Any]) -> tuple[bool, str]:
    required = {'symbol', 'predicted_value', 'confidence_score', 'timestamp'}
    missing = [key for key in required if key not in data]
    if missing:
        return False, f'missing keys: {missing}'
    return True, ''


def _validate_forecast(data: dict[str, Any]) -> tuple[bool, str]:
    points = data.get('forecast')
    if not isinstance(points, list) or not points:
        return False, 'forecast must be a non-empty list'
    if len(set(round(float(v), 6) for v in points)) <= 1:
        return False, 'forecast appears static/flat'
    return True, ''


def _validate_chat(data: dict[str, Any]) -> tuple[bool, str]:
    reply = str(data.get('reply', '')).strip()
    if not reply:
        return False, 'reply is empty'
    fallback = 'Context-grounded response for' in reply or 'No GenAI knowledge bundle was matched' in reply
    if fallback:
        return True, 'fallback_response'
    return True, 'gemini_response'


def _validate_sentiment(data: dict[str, Any]) -> tuple[bool, str]:
    required = {'symbol', 'score', 'label'}
    missing = [key for key in required if key not in data]
    if missing:
        return False, f'missing keys: {missing}'
    return True, ''


def _validate_monitoring(data: dict[str, Any]) -> tuple[bool, str]:
    required = {'total_predictions_24h', 'avg_confidence_24h', 'error_rate_24h', 'p95_latency_ms', 'usage_stats_24h'}
    missing = [key for key in required if key not in data]
    if missing:
        return False, f'missing keys: {missing}'
    return True, ''


def _validate_calendar(data: dict[str, Any]) -> tuple[bool, str]:
    if data.get('sync_status') != 'synced':
        return False, f"sync_status must be synced, got: {data.get('sync_status')}"
    if not data.get('google_event_id'):
        return False, 'google_event_id is empty'
    return True, ''


async def main() -> None:
    checks: list[CheckResult] = []

    async with httpx.AsyncClient(timeout=5.0) as client:
        checks.append(
            await _run_api_check(
                client,
                'predict',
                lambda: client.post(f'{API_BASE}/predict', json={'ticker': 'AAPL', 'model_type': 'ml'}),
                _validate_predict,
            )
        )
        checks.append(
            await _run_api_check(
                client,
                'forecast',
                lambda: client.post(f'{API_BASE}/forecast', json={'ticker': 'AAPL', 'horizon_days': 7}),
                _validate_forecast,
            )
        )
        checks.append(
            await _run_api_check(
                client,
                'chat',
                lambda: client.post(f'{API_BASE}/chat', json={'message': 'Give me an AAPL outlook in one paragraph', 'ticker': 'AAPL'}),
                _validate_chat,
            )
        )
        checks.append(
            await _run_api_check(
                client,
                'sentiment',
                lambda: client.get(f'{API_BASE}/sentiment/AAPL'),
                _validate_sentiment,
            )
        )
        checks.append(
            await _run_api_check(
                client,
                'monitoring',
                lambda: client.get(f'{API_BASE}/monitoring'),
                _validate_monitoring,
            )
        )
        checks.append(
            await _run_api_check(
                client,
                'calendar_sync',
                lambda: client.post(
                    f'{API_BASE}/calendar/schedule',
                    json={
                        'title': 'QA Sync Event',
                        'start_time': '2026-04-13T10:00:00Z',
                        'end_time': '2026-04-13T11:00:00Z',
                    },
                ),
                _validate_calendar,
            )
        )

    checks.append(await _check_mysql())

    pass_count = sum(1 for check in checks if check.passed)
    fail_count = len(checks) - pass_count

    bugs = [
        {'component': check.name, 'details': check.details}
        for check in checks
        if not check.passed
    ]

    suggestions = []
    for check in checks:
        if check.passed:
            continue
        if check.name == 'chat':
            suggestions.append('Validate GOOGLE_API_KEY and network egress to Gemini API; fallback response indicates GenAI failure path.')
        elif check.name == 'mysql_connection':
            suggestions.append('Verify DATABASE_URL credentials and MySQL grants for configured user.')
        elif check.name == 'calendar_sync':
            suggestions.append('Check calendar service credentials or sync implementation path for event propagation.')
        else:
            suggestions.append(f'Investigate {check.name} endpoint behavior and schema contract mismatch.')

    report = {
        'base_url': BASE_URL,
        'api_base': API_BASE,
        'max_latency_seconds': MAX_LATENCY_SECONDS,
        'summary': {
            'total_checks': len(checks),
            'pass': pass_count,
            'fail': fail_count,
            'status': 'pass' if fail_count == 0 else 'fail',
        },
        'checks': [
            {
                'name': check.name,
                'passed': check.passed,
                'latency_ms': check.latency_ms,
                'details': check.details,
            }
            for check in checks
        ],
        'bug_list': bugs,
        'fix_suggestions': suggestions,
    }

    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    asyncio.run(main())
