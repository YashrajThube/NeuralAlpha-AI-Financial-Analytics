"""Basic staging smoke tests for NeuralAlpha deployed stack."""

from __future__ import annotations

import json
from typing import Any

import httpx

BASE_URL = "http://127.0.0.1:8000"


def _assert_status(resp: httpx.Response, expected: int = 200) -> None:
    if resp.status_code != expected:
        raise RuntimeError(f"Unexpected status {resp.status_code} for {resp.request.url}: {resp.text}")


def _assert_keys(payload: dict[str, Any], keys: list[str], name: str) -> None:
    missing = [k for k in keys if k not in payload]
    if missing:
        raise RuntimeError(f"{name} missing keys: {missing}")


def _unwrap_envelope(resp: httpx.Response, name: str) -> dict[str, Any]:
    _assert_status(resp)
    payload = resp.json()
    _assert_keys(payload, ["success", "data", "error"], f"{name}-envelope")
    if payload.get("success") is not True:
        raise RuntimeError(f"{name} returned unsuccessful payload: {payload}")
    if payload.get("error") is not None:
        raise RuntimeError(f"{name} returned unexpected error: {payload}")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError(f"{name} data must be object, got: {type(data).__name__}")
    return data


def main() -> None:
    report: dict[str, Any] = {}
    with httpx.Client(timeout=20.0) as client:
        health = client.get(f"{BASE_URL}/health")
        _assert_status(health)
        report["health"] = health.json()

        sentiment_payload = _unwrap_envelope(client.get(f"{BASE_URL}/api/v1/sentiment/AAPL"), "sentiment")
        _assert_keys(sentiment_payload, ["symbol", "score", "label"], "sentiment")
        report["sentiment"] = sentiment_payload

        predict_payload = _unwrap_envelope(
            client.post(
                f"{BASE_URL}/api/v1/predict",
                json={"ticker": "AAPL", "model_type": "ml"},
            ),
            "predict",
        )
        _assert_keys(
            predict_payload,
            ["symbol", "predicted_value", "confidence_score", "timestamp"],
            "predict",
        )
        report["predict"] = predict_payload

        forecast_payload = _unwrap_envelope(
            client.post(
                f"{BASE_URL}/api/v1/forecast",
                json={"ticker": "AAPL", "horizon_days": 5},
            ),
            "forecast",
        )
        _assert_keys(forecast_payload, ["symbol", "horizon_days", "forecast"], "forecast")
        report["forecast"] = forecast_payload

        chat_payload = _unwrap_envelope(
            client.post(
                f"{BASE_URL}/api/v1/chat",
                json={"message": "Give me a quick AAPL summary", "ticker": "AAPL"},
            ),
            "chat",
        )
        _assert_keys(chat_payload, ["reply", "symbol"], "chat")
        report["chat"] = chat_payload

        monitoring_payload = _unwrap_envelope(client.get(f"{BASE_URL}/api/v1/monitoring"), "monitoring")
        _assert_keys(
            monitoring_payload,
            ["total_predictions_24h", "avg_confidence_24h", "error_rate_24h", "p95_latency_ms", "usage_stats_24h"],
            "monitoring",
        )
        report["monitoring"] = monitoring_payload

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
