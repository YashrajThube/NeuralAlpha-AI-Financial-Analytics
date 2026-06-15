"""Strict production validation report for NeuralAlpha full-stack system."""

from __future__ import annotations

import json
from typing import Any

import httpx

BACKEND_BASE = "http://127.0.0.1:8000"
FRONTEND_BASE = "http://127.0.0.1:5173"


def _is_number(value: Any) -> bool:
    try:
        float(value)
    except Exception:
        return False
    return True


def _safe_post(client: httpx.Client, url: str, payload: dict[str, Any]) -> tuple[bool, dict[str, Any] | None]:
    try:
        resp = client.post(url, json=payload, timeout=15.0)
        if resp.status_code != 200:
            return False, None
        return True, resp.json()
    except Exception:
        return False, None


def _safe_get(client: httpx.Client, url: str) -> tuple[bool, dict[str, Any] | None]:
    try:
        resp = client.get(url, timeout=15.0)
        if resp.status_code != 200:
            return False, None
        return True, resp.json()
    except Exception:
        return False, None


def _unwrap_envelope(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    if payload.get('success') is True and isinstance(payload.get('data'), dict):
        return payload['data']
    return None


def main() -> None:
    result = {
        "ml_valid": False,
        "dl_valid": False,
        "genai_valid": False,
        "api_valid": False,
        "api_v1_valid": False,
        "api_compat_valid": False,
        "frontend_valid": False,
        "e2e_status": "fail",
        "details": {},
    }

    with httpx.Client() as client:
        # Primary contract checks: /api/v1 with envelope responses.
        v1_predict_ok, v1_predict_raw = _safe_post(
            client,
            f"{BACKEND_BASE}/api/v1/predict",
            {
                "symbol": "AAPL",
                "model_type": "ml",
            },
        )
        v1_predict_data = _unwrap_envelope(v1_predict_raw)

        v1_forecast_ok, v1_forecast_raw = _safe_post(
            client,
            f"{BACKEND_BASE}/api/v1/forecast",
            {
                "symbol": "AAPL",
                "horizon_days": 5,
            },
        )
        v1_forecast_data = _unwrap_envelope(v1_forecast_raw)

        v1_chat_ok, v1_chat_raw = _safe_post(
            client,
            f"{BACKEND_BASE}/api/v1/chat",
            {
                "message": "Give me a short AAPL outlook",
                "symbol": "AAPL",
            },
        )
        v1_chat_data = _unwrap_envelope(v1_chat_raw)

        v1_monitor_ok, v1_monitor_raw = _safe_get(
            client,
            f"{BACKEND_BASE}/api/v1/monitoring",
        )
        v1_monitor_data = _unwrap_envelope(v1_monitor_raw)

        v1_contract_ok = all([
            v1_predict_ok,
            v1_forecast_ok,
            v1_chat_ok,
            v1_monitor_ok,
            isinstance(v1_predict_data, dict),
            isinstance(v1_forecast_data, dict),
            isinstance(v1_chat_data, dict),
            isinstance(v1_monitor_data, dict),
        ])

        if v1_contract_ok and v1_predict_data and v1_forecast_data and v1_chat_data and v1_monitor_data:
            v1_contract_ok = all(
                [
                    {'symbol', 'predicted_value', 'confidence_score', 'timestamp'}.issubset(v1_predict_data.keys()),
                    {'symbol', 'horizon_days', 'forecast'}.issubset(v1_forecast_data.keys()),
                    {'reply', 'symbol'}.issubset(v1_chat_data.keys()),
                    {'total_predictions_24h', 'avg_confidence_24h', 'error_rate_24h', 'p95_latency_ms'}.issubset(v1_monitor_data.keys()),
                ]
            )

        result['api_v1_valid'] = v1_contract_ok
        result['details']['api_v1_checks'] = {
            'predict_ok': v1_predict_ok,
            'forecast_ok': v1_forecast_ok,
            'chat_ok': v1_chat_ok,
            'monitor_ok': v1_monitor_ok,
        }

        # Secondary compatibility checks: /api legacy responses.
        compat_predict_a_ok, compat_predict_a = _safe_post(
            client,
            f"{BACKEND_BASE}/api/predict",
            {
                "sequence": [181.2, 182.1, 183.4, 184.0, 184.3, 184.7, 185.0, 185.3, 185.1, 185.6],
                "symbol": "AAPL",
            },
        )
        compat_predict_b_ok, compat_predict_b = _safe_post(
            client,
            f"{BACKEND_BASE}/api/predict",
            {
                "sequence": [120.1, 121.0, 119.8, 118.6, 117.9, 118.2, 118.7, 119.0, 118.8, 118.4],
                "symbol": "TSLA",
            },
        )

        compat_forecast_ok, compat_forecast = _safe_post(
            client,
            f"{BACKEND_BASE}/api/forecast",
            {
                "symbol": "AAPL",
                "horizon": 5,
                "sequence": [181.2, 182.1, 183.4, 184.0, 184.3, 184.7, 185.0, 185.3, 185.1, 185.6],
            },
        )

        compat_insight_a_ok, compat_insight_a = _safe_post(
            client,
            f"{BACKEND_BASE}/api/ai-insight",
            {"question": "What is the near-term outlook for AAPL?", "top_k": 3},
        )
        compat_insight_b_ok, compat_insight_b = _safe_post(
            client,
            f"{BACKEND_BASE}/api/ai-insight",
            {"question": "What is the downside risk for TSLA this week?", "top_k": 3},
        )

        monitor_ok = False
        monitor: dict[str, Any] | None = None
        try:
            monitor_resp = client.get(f"{BACKEND_BASE}/api/monitoring/summary", timeout=10.0)
            monitor_ok = monitor_resp.status_code == 200
            monitor = monitor_resp.json() if monitor_ok else None
        except Exception:
            monitor_ok = False

        compat_contract_ok = all([compat_predict_a_ok, compat_forecast_ok, compat_insight_a_ok, monitor_ok])
        if compat_contract_ok and compat_predict_a and compat_forecast and compat_insight_a and monitor:
            required_predict = {
                "prediction",
                "confidence",
                "model_version",
                "ai_explanation",
                "fallback_used",
            }
            required_forecast = {
                "next_value",
                "confidence",
                "multi_step_forecast",
                "latency_ms",
                "fallback_used",
            }
            required_insight = {"trend", "risk", "recommendation"}
            required_monitor = {
                "rolling_mae",
                "rolling_mse",
                "avg_latency_ms",
                "p95_latency_ms",
                "error_rate",
                "mae_alert",
                "latency_alert",
            }
            compat_contract_ok = (
                required_predict.issubset(compat_predict_a.keys())
                and required_forecast.issubset(compat_forecast.keys())
                and required_insight.issubset(compat_insight_a.keys())
                and required_monitor.issubset(monitor.keys())
            )

        result['api_compat_valid'] = compat_contract_ok
        result['details']['api_compat_checks'] = {
            'predict_a_ok': compat_predict_a_ok,
            'predict_b_ok': compat_predict_b_ok,
            'forecast_ok': compat_forecast_ok,
            'insight_a_ok': compat_insight_a_ok,
            'insight_b_ok': compat_insight_b_ok,
            "monitor_ok": monitor_ok,
        }

        result['api_valid'] = bool(result['api_v1_valid'] and result['api_compat_valid'])

        if compat_predict_a_ok and compat_predict_b_ok and compat_predict_a and compat_predict_b:
            preds_differ = float(compat_predict_a["prediction"]) != float(compat_predict_b["prediction"])
            real_model = not str(compat_predict_a.get("model_version", "")).startswith("fallback")
            result["ml_valid"] = real_model and _is_number(compat_predict_a.get("confidence"))
            result["details"]["ml"] = {
                "preds_differ": preds_differ,
                "real_model": real_model,
                "model_version": compat_predict_a.get("model_version"),
            }

        if compat_forecast_ok and compat_forecast:
            arr = compat_forecast.get("multi_step_forecast") or []
            fallback_used = bool(compat_forecast.get("fallback_used", False))
            result["dl_valid"] = (
                isinstance(arr, list)
                and len(arr) >= 3
                and len(set(round(float(v), 6) for v in arr)) > 1
                and not fallback_used
            )
            result["details"]["dl"] = {
                "horizon_len": len(arr) if isinstance(arr, list) else 0,
                "model_version": compat_forecast.get("model_version"),
                "fallback_used": fallback_used,
            }

        if compat_insight_a_ok and compat_insight_b_ok and compat_insight_a and compat_insight_b:
            dynamic = compat_insight_a != compat_insight_b
            shape_ok = all(k in compat_insight_a for k in ("trend", "risk", "recommendation"))
            result["genai_valid"] = shape_ok and dynamic
            result["details"]["genai"] = {
                "shape_ok": shape_ok,
                "dynamic": dynamic,
            }

        try:
            proxy_predict = client.post(
                f"{FRONTEND_BASE}/api/v1/predict",
                json={
                    "symbol": "AAPL",
                    "model_type": "ml",
                },
                timeout=10.0,
            )
            result["frontend_valid"] = proxy_predict.status_code == 200
            result["details"]["frontend_proxy_status"] = proxy_predict.status_code
        except Exception:
            result["frontend_valid"] = False
            result["details"]["frontend_proxy_status"] = None

    # E2E status is inferred from strict functional checks unless dedicated playwright run is performed.
    result["e2e_status"] = "pass" if all([
        result["ml_valid"],
        result["dl_valid"],
        result["genai_valid"],
        result["api_valid"],
        result["frontend_valid"],
    ]) else "fail"

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
