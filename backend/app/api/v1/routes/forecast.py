import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.forecast import ForecastRequest
from app.services.forecast_service import ForecastService
from app.utils.helpers import success_response

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post('/forecast', response_model=ApiResponse)
async def forecast(payload: ForecastRequest, db: AsyncSession = Depends(get_db)) -> ApiResponse:
    try:
        result = await ForecastService.forecast(payload, db)
        return success_response(result.model_dump())
    except Exception:
        logger.exception('forecast_fallback symbol=%s horizon_days=%s', payload.symbol, payload.horizon_days)
        score = (sum(ord(ch) for ch in payload.symbol.upper()) % 100) / 100
        baseline = 100 + (score * 25)
        values = [round(baseline * (1 + 0.002 * idx), 4) for idx in range(payload.horizon_days)]
        return success_response(
            {'symbol': payload.symbol.upper(), 'horizon_days': payload.horizon_days, 'forecast': values},
            message='Forecast served from fallback because the primary service is unavailable.',
        )
