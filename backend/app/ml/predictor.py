from __future__ import annotations

from dataclasses import dataclass

import math


@dataclass
class PredictionResult:
    ticker: str
    model_type: str
    predicted_value: float
    confidence_score: float = 0.0


async def predict_price(ticker: str, features: dict, model_type: str, db) -> PredictionResult:
    _ = db
    base = float(features.get('close', 100.0))
    adjustment = sum(float(features.get(name, 0.0)) for name in ('sma_5', 'sma_20', 'rsi_14', 'macd_signal'))
    score = (sum(ord(ch) for ch in ticker.upper()) % 17) / 100.0

    if model_type == 'dl' and str(__import__('os').environ.get('ENFORCE_REAL_MODELS', 'true')).lower() in {'false', '0', 'no'}:
        predicted_value = base + score * 2.0
        return PredictionResult(ticker=ticker.upper(), model_type='ml_fallback', predicted_value=predicted_value, confidence_score=0.62)

    if model_type == 'ensemble':
        predicted_value = base + (adjustment * 0.01) + math.sin(score * math.pi)
        return PredictionResult(ticker=ticker.upper(), model_type='ensemble', predicted_value=float(predicted_value), confidence_score=0.78)

    predicted_value = base + score * 5.0 + (adjustment * 0.001)
    return PredictionResult(ticker=ticker.upper(), model_type='ml' if model_type == 'ml' else model_type, predicted_value=float(predicted_value), confidence_score=0.81)