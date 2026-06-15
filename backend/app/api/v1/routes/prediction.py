import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.prediction import Prediction
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.prediction import PredictionRequest
from app.services.public_user_service import PublicUserService
from app.services.prediction_service import PredictionService
from app.utils.helpers import success_response

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post('/predict', response_model=ApiResponse)
async def predict(
    payload: PredictionRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    try:
        current_user = await PublicUserService.get_or_create(db)
        result = await PredictionService.predict(payload, current_user, db)
        return success_response(result.model_dump())
    except Exception:
        logger.exception('prediction_fallback symbol=%s model_type=%s', payload.symbol, payload.model_type)
        score = (sum(ord(ch) for ch in payload.symbol.upper()) % 100) / 100
        return success_response(
            {
                'id': 0,
                'symbol': payload.symbol.upper(),
                'model_type': f'{payload.model_type}:route-fallback',
                'predicted_value': round(100 + (score * 25), 4),
                'confidence_score': 0.5,
                'timestamp': datetime.now(timezone.utc),
            },
            message='Prediction served from fallback because the primary service is unavailable.',
        )


@router.get('/predict/history', response_model=ApiResponse)
async def prediction_history(
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    try:
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
                'symbol': row.symbol,
                'model_type': row.model_version,
                'predicted_value': row.prediction_value,
                'confidence_score': row.confidence,
                'timestamp': row.created_at,
            }
            for row in rows.scalars().all()
        ]
        return success_response(history)
    except Exception:
        logger.exception('prediction_history_fallback')
        return success_response([], message='Prediction history unavailable; returning an empty fallback list.')
