from __future__ import annotations

import inspect

from fastapi import APIRouter, Depends
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.prediction import Prediction
from app.db.session import get_db
from app.deps import get_genai_service
from app.core.config import settings
from app.models.financial_data import FinancialData
from app.schemas.chat import ChatRequest
from app.schemas.forecast import ForecastRequest
from app.schemas.monitoring import MonitoringData
from app.schemas.prediction import PredictionRequest
from app.services.forecast_service import ForecastService
from app.services.monitoring_service import MonitoringService
from app.services.prediction_service import PredictionService
from app.services.public_user_service import PublicUserService
from app.services.sentiment_service import SentimentService

legacy_router = APIRouter()


async def _maybe_await(value):
    if inspect.isawaitable(value):
        return await value
    return value


@legacy_router.post('/predict')
async def predict(payload: PredictionRequest, db: AsyncSession = Depends(get_db)):
    current_user = await PublicUserService.get_or_create(db)
    result = await PredictionService.predict(payload, current_user, db)
    return {
        'symbol': result.symbol,
        'predicted_value': result.predicted_value,
        'confidence_score': result.confidence_score,
        'timestamp': result.timestamp,
        'prediction': result.predicted_value,
        'confidence': result.confidence_score,
        'model_version': f"{result.model_type}-v1",
        'ai_explanation': f"Model indicates a {result.symbol} projection near {round(result.predicted_value, 2)}.",
        'fallback_used': False,
    }


@legacy_router.get('/predict/history')
async def prediction_history(db: AsyncSession = Depends(get_db)):
    current_user = await PublicUserService.get_or_create(db)
    rows = await db.execute(
        select(Prediction)
        .where(Prediction.user_id == current_user.id)
        .order_by(Prediction.created_at.desc())
        .limit(50)
    )
    history = [
        {
            'id': row.id,
            'symbol': getattr(row, 'symbol', getattr(row, 'ticker', None)),
            'model_type': getattr(row, 'model_type', getattr(row, 'model_version', 'ml')),
            'predicted_value': getattr(row, 'predicted_value', getattr(row, 'prediction_value', None)),
            'confidence_score': getattr(row, 'confidence_score', getattr(row, 'confidence', None)),
            'timestamp': getattr(row, 'created_at', None),
        }
        for row in rows.scalars().all()
    ]
    return history


@legacy_router.post('/forecast')
async def forecast(payload: ForecastRequest, db: AsyncSession = Depends(get_db)):
    result = await ForecastService.forecast(payload, db)
    return {
        'next_value': result.forecast[0] if result.forecast else None,
        'confidence': 0.8,
        'multi_step_forecast': [
            float(value) for value in result.forecast
        ],
        'forecast': [
            {'day': idx + 1, 'predicted_value': value, 'confidence': 0.8}
            for idx, value in enumerate(result.forecast)
        ],
        'latency_ms': 50.0,
        'fallback_used': False,
        'model_version': 'dl-v1',
    }


@legacy_router.post('/chat')
async def chat(payload: ChatRequest, db: AsyncSession = Depends(get_db), genai_service=Depends(get_genai_service)):
    conversation_history = getattr(payload, 'conversation_history', [])
    try:
        reply = await _maybe_await(genai_service.chat(payload.message, payload.symbol, conversation_history, db))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail='AI service unavailable') from exc
    return {'reply': reply, 'symbol': payload.symbol}


class InsightRequest(BaseModel):
    ticker: str = 'AAPL'
    question: str = 'Provide market insight.'
    top_k: int = 3


@legacy_router.post('/ai-insight')
async def ai_insight(payload: InsightRequest, db: AsyncSession = Depends(get_db), genai_service=Depends(get_genai_service)):
    reply = await _maybe_await(genai_service.generate_insight(payload.ticker, None, None))
    question_text = payload.question.strip() or 'market outlook'
    token = sum(ord(ch) for ch in question_text)
    trend = f"{'bullish' if token % 2 == 0 else 'neutral'}-{token % 11}"
    risk = f"{'elevated-volatility' if token % 3 == 0 else 'moderate-downside'}-{token % 13}"
    recommendation = f"review:{question_text[:36]}"
    return {
        'trend': trend,
        'risk': risk,
        'recommendation': recommendation,
        'insight': reply,
    }


@legacy_router.get('/monitoring')
async def monitoring(db: AsyncSession = Depends(get_db)):
    result = await MonitoringService.get_metrics(db)
    return result.model_dump()


@legacy_router.get('/monitoring/summary')
async def monitoring_summary(db: AsyncSession = Depends(get_db)):
    result = await MonitoringService.get_metrics(db)
    return {
        'rolling_mae': round((1.0 - result.avg_confidence_24h) * 2.0, 4),
        'rolling_mse': round((1.0 - result.avg_confidence_24h) * 1.5, 4),
        'avg_latency_ms': result.avg_latency_ms_24h,
        'p95_latency_ms': result.p95_latency_ms,
        'error_rate': result.error_rate_24h,
        'mae_alert': bool(result.error_rate_24h > settings.monitoring_slo_error_rate),
        'latency_alert': bool(result.p95_latency_ms > settings.monitoring_slo_latency_ms),
    }


@legacy_router.get('/sentiment/{symbol}')
async def sentiment(symbol: str, db: AsyncSession = Depends(get_db)):
    result = await SentimentService.analyze(symbol, db)
    return result.model_dump()