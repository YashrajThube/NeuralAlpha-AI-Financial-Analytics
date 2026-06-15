"""Simple async load test for /api/v1 endpoints.

Targets at least ~10 requests/second and reports p95 latency and error rate.
"""

from __future__ import annotations

import asyncio
import argparse
import json
import time
from collections import defaultdict

import httpx

BASE_URL = 'http://127.0.0.1:8000/api/v1'
DEFAULT_REQUESTS_PER_SECOND = 10
DEFAULT_DURATION_SECONDS = 12


async def _send(client: httpx.AsyncClient, endpoint: str, payload: dict | None) -> tuple[str, float, int]:
    started = time.perf_counter()
    try:
        if payload is None:
            resp = await client.get(f'{BASE_URL}{endpoint}')
        else:
            resp = await client.post(f'{BASE_URL}{endpoint}', json=payload)
        latency_ms = (time.perf_counter() - started) * 1000
        return endpoint, latency_ms, resp.status_code
    except Exception:
        latency_ms = (time.perf_counter() - started) * 1000
        return endpoint, latency_ms, 599


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    idx = int(round(0.95 * (len(values) - 1)))
    return float(values[idx])


def _p99(values: list[float]) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    idx = int(round(0.99 * (len(values) - 1)))
    return float(values[idx])


async def run_load_test(requests_per_second: int, duration_seconds: int) -> None:
    endpoints = [
        ('/predict', {'ticker': 'AAPL', 'model_type': 'ml'}),
        ('/forecast', {'ticker': 'AAPL', 'horizon_days': 5}),
        ('/chat', {'message': 'Give me one-line outlook for AAPL', 'ticker': 'AAPL'}),
        ('/sentiment/AAPL', None),
        ('/monitoring', None),
    ]

    results: list[tuple[str, float, int]] = []

    async with httpx.AsyncClient(timeout=8.0) as client:
        started = time.perf_counter()
        all_tasks: list[asyncio.Task] = []
        total_requests = requests_per_second * duration_seconds

        for n in range(total_requests):
            endpoint, payload = endpoints[n % len(endpoints)]
            all_tasks.append(asyncio.create_task(_send(client, endpoint, payload)))
            target_time = started + ((n + 1) / requests_per_second)
            delay = target_time - time.perf_counter()
            if delay > 0:
                await asyncio.sleep(delay)

        if all_tasks:
            results.extend(await asyncio.gather(*all_tasks, return_exceptions=False))

    by_endpoint = defaultdict(list)
    by_status = defaultdict(int)
    failures = 0
    for endpoint, latency, status in results:
        by_endpoint[endpoint].append(latency)
        by_status[str(status)] += 1
        if status != 200:
            failures += 1

    endpoint_metrics = {
        endpoint: {
            'count': len(values),
            'avg_latency_ms': round(sum(values) / len(values), 3),
            'p95_latency_ms': round(_p95(values), 3),
            'p99_latency_ms': round(_p99(values), 3),
        }
        for endpoint, values in by_endpoint.items()
    }

    max_p95_ms = max((m['p95_latency_ms'] for m in endpoint_metrics.values()), default=0.0)
    chat_p95_ms = endpoint_metrics.get('/chat', {}).get('p95_latency_ms', 0.0)
    sla = {
        'all_api_under_3s_p95': max_p95_ms < 3000.0,
        'chat_under_2s_p95': chat_p95_ms < 2000.0,
    }

    summary = {
        'requests_per_second': requests_per_second,
        'duration_seconds': duration_seconds,
        'total_requests': len(results),
        'failures': failures,
        'error_rate': round((failures / len(results)) if results else 0.0, 4),
        'status_codes': dict(by_status),
        'endpoint_metrics': endpoint_metrics,
        'sla': sla,
    }

    print(json.dumps(summary, indent=2))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Load test /api/v1 endpoints.')
    parser.add_argument('--rps', type=int, default=DEFAULT_REQUESTS_PER_SECOND, help='Requests per second (10-50 recommended).')
    parser.add_argument('--duration', type=int, default=DEFAULT_DURATION_SECONDS, help='Test duration in seconds.')
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    asyncio.run(run_load_test(args.rps, args.duration))
