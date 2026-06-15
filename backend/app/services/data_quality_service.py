from __future__ import annotations

import math


class DataQualityService:
    @staticmethod
    def sanitize_prediction(value: float, confidence: float) -> tuple[float, float]:
        safe_value = float(value)
        safe_conf = float(confidence)

        if not math.isfinite(safe_value) or safe_value <= 0:
            safe_value = 100.0
        if not math.isfinite(safe_conf):
            safe_conf = 0.5
        safe_conf = min(max(safe_conf, 0.0), 1.0)
        return safe_value, safe_conf

    @staticmethod
    def sanitize_forecast(series: list[float]) -> list[float]:
        cleaned = [float(v) for v in series if math.isfinite(float(v)) and float(v) > 0]
        if not cleaned:
            return [100.0]
        return cleaned

    @staticmethod
    def sanitize_sentiment(score: float, label: str) -> tuple[float, str]:
        safe_score = float(score)
        if not math.isfinite(safe_score):
            safe_score = 0.0
        safe_score = min(max(safe_score, -1.0), 1.0)

        safe_label = str(label or 'Neutral').strip() or 'Neutral'
        if safe_label not in {'Positive', 'Negative', 'Neutral'}:
            safe_label = 'Neutral'
        return safe_score, safe_label
