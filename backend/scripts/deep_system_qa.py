from __future__ import annotations

import asyncio
import json
import time
import sys
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import settings

BASE_URL = "http://127.0.0.1:8000"


def _unwrap_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("success") is not True:
        raise RuntimeError(f"Envelope indicates failure: {payload}")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError(f"Envelope data should be object, got: {type(data).__name__}")
    return data


async def _db_snapshot(symbol: str) -> dict[str, Any]:
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    try:
        async with engine.connect() as conn:
            count_result = await conn.execute(
                text("SELECT COUNT(*) AS c FROM predictions WHERE symbol = :symbol"),
                {"symbol": symbol},
            )
            count = int(count_result.scalar_one() or 0)

            model_result = await conn.execute(
                text(
                    """
                    SELECT message
                    FROM logs
                    WHERE action = 'prediction.request'
                    ORDER BY id DESC
                    LIMIT 1
                    """
                )
            )
            message = model_result.scalar_one_or_none()
            model_version = None
            if message:
                try:
                    model_version = json.loads(message).get("model_version")
                except Exception:
                    model_version = None

            return {"prediction_count": count, "latest_model_version": model_version}
    finally:
        await engine.dispose()


def _label_matches_score(score: float, label: str) -> bool:
    if score > 0.1:
        return label.lower() == "positive"
    if score < -0.1:
        return label.lower() == "negative"
    return label.lower() == "neutral"


async def main() -> None:
    result: dict[str, Any] = {
        "prediction": {},
        "forecast": {},
        "chat": {},
        "sentiment": {},
        "monitoring": {},
        "real_vs_fake": {},
        "accuracy_sanity": {},
        "fix_list": [],
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        insert_symbol = f"QA{int(time.time()) % 100000}"
        before_db = await _db_snapshot(insert_symbol)
        before_monitor = _unwrap_envelope((await client.get(f"{BASE_URL}/api/v1/monitoring")).json())

        pred_a = _unwrap_envelope(
            (
                await client.post(
                    f"{BASE_URL}/api/v1/predict",
                    json={"symbol": "AAPL", "model_type": "ml"},
                )
            ).json()
        )
        pred_b = _unwrap_envelope(
            (
                await client.post(
                    f"{BASE_URL}/api/v1/predict",
                    json={"symbol": "TSLA", "model_type": "ml"},
                )
            ).json()
        )

        _ = _unwrap_envelope(
            (
                await client.post(
                    f"{BASE_URL}/api/v1/predict",
                    json={"symbol": insert_symbol, "model_type": "ml"},
                )
            ).json()
        )

        after_db = await _db_snapshot(insert_symbol)

        forecast = _unwrap_envelope(
            (
                await client.post(
                    f"{BASE_URL}/api/v1/forecast",
                    json={"symbol": "AAPL", "horizon_days": 7},
                )
            ).json()
        )

        chat_1 = _unwrap_envelope(
            (
                await client.post(
                    f"{BASE_URL}/api/v1/chat",
                    json={"symbol": "AAPL", "message": "Give me a short bullish case for AAPL"},
                )
            ).json()
        )
        chat_2 = _unwrap_envelope(
            (
                await client.post(
                    f"{BASE_URL}/api/v1/chat",
                    json={"symbol": "AAPL", "message": "Give me the downside risk case for AAPL this week"},
                )
            ).json()
        )

        sentiment = _unwrap_envelope((await client.get(f"{BASE_URL}/api/v1/sentiment/AAPL")).json())

        after_monitor = _unwrap_envelope((await client.get(f"{BASE_URL}/api/v1/monitoring")).json())

    prediction_dynamic = float(pred_a["predicted_value"]) != float(pred_b["predicted_value"])
    db_insert_ok = int(after_db["prediction_count"]) > int(before_db["prediction_count"])

    series = forecast.get("forecast", [])
    unique_points = len(set(round(float(v), 8) for v in series)) if isinstance(series, list) else 0
    forecast_dynamic = isinstance(series, list) and len(series) >= 3 and unique_points > 1

    chat_dynamic = chat_1.get("reply", "").strip() != chat_2.get("reply", "").strip()

    sentiment_score = float(sentiment.get("score", 0.0))
    sentiment_label = str(sentiment.get("label", ""))
    sentiment_consistent = _label_matches_score(sentiment_score, sentiment_label)

    before_usage = before_monitor.get("usage_stats_24h", {}) or {}
    after_usage = after_monitor.get("usage_stats_24h", {}) or {}
    pred_before = int(before_usage.get("prediction.request", 0))
    pred_after = int(after_usage.get("prediction.request", 0))
    chat_before = int(before_usage.get("chat.request", 0))
    chat_after = int(after_usage.get("chat.request", 0))
    monitoring_updated = (pred_after > pred_before) or (chat_after > chat_before)

    latest_model_version = str(after_db.get("latest_model_version") or "unknown")
    likely_real_model = ("missing" not in latest_model_version.lower()) and ("fallback" not in latest_model_version.lower())

    confidence_ok = 0.0 <= float(pred_a.get("confidence_score", 0.0)) <= 1.0
    predicted_positive = float(pred_a.get("predicted_value", 0.0)) > 0

    result["prediction"] = {
        "aapl_predicted_value": pred_a.get("predicted_value"),
        "tsla_predicted_value": pred_b.get("predicted_value"),
        "dynamic_output": prediction_dynamic,
        "db_insert_validated": db_insert_ok,
        "db_insert_symbol": insert_symbol,
        "db_count_before": before_db.get("prediction_count"),
        "db_count_after": after_db.get("prediction_count"),
    }
    result["forecast"] = {
        "horizon_points": len(series) if isinstance(series, list) else 0,
        "unique_points": unique_points,
        "time_series_non_flat": forecast_dynamic,
    }
    result["chat"] = {
        "prompt_1_reply_len": len(chat_1.get("reply", "")),
        "prompt_2_reply_len": len(chat_2.get("reply", "")),
        "dynamic_responses": chat_dynamic,
    }
    result["sentiment"] = {
        "score": sentiment_score,
        "label": sentiment_label,
        "label_matches_score": sentiment_consistent,
    }
    result["monitoring"] = {
        "prediction_request_before": pred_before,
        "prediction_request_after": pred_after,
        "chat_request_before": chat_before,
        "chat_request_after": chat_after,
        "values_updated": monitoring_updated,
    }
    result["real_vs_fake"] = {
        "latest_prediction_model_version": latest_model_version,
        "likely_real_model": likely_real_model,
    }
    result["accuracy_sanity"] = {
        "confidence_in_range": confidence_ok,
        "predicted_value_positive": predicted_positive,
        "forecast_dynamic": forecast_dynamic,
        "sentiment_consistent": sentiment_consistent,
    }

    if not prediction_dynamic:
        result["fix_list"].append("Prediction appears constant across symbols. Recheck feature inputs and model fallback logic in PredictionService.")
    if not db_insert_ok:
        result["fix_list"].append("Prediction DB insert did not increase row count. Check DB transaction commit path and SQL insert in PredictionService.")
    if not forecast_dynamic:
        result["fix_list"].append("Forecast appears flat. Check market data retrieval and drift calculation in ForecastService.")
    if not chat_dynamic:
        result["fix_list"].append("Chat responses are not dynamic enough. Improve prompt conditioning and retrieval context mixing in ChatService.")
    if not sentiment_consistent:
        result["fix_list"].append("Sentiment label mismatch with score thresholds. Fix labeling function in SentimentService.")
    if not monitoring_updated:
        result["fix_list"].append("Monitoring counters did not update after live traffic. Verify log writes and aggregation in MonitoringService.")
    if not likely_real_model:
        result["fix_list"].append("Model version suggests fallback/missing artifacts. Verify model files and model loader resolution paths.")

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
