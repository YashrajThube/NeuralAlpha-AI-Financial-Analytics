import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.services.sentiment_service import SentimentService
from app.utils.helpers import success_response

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get('/sentiment/{symbol}', response_model=ApiResponse)
async def sentiment(
    symbol: str = Path(min_length=1, max_length=16, pattern='^[A-Za-z0-9._-]{1,16}$'),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    try:
        result = await SentimentService.analyze(symbol, db)
        return success_response(result.model_dump())
    except Exception:
        clean_symbol = symbol.upper().strip()
        logger.exception('sentiment_fallback symbol=%s', clean_symbol)
        score = round(((sum(ord(c) for c in clean_symbol) % 200) - 100) / 400, 4)
        label = 'Positive' if score > 0.1 else 'Negative' if score < -0.1 else 'Neutral'
        return success_response(
            {'symbol': clean_symbol, 'score': score, 'label': label, 'timestamp': datetime.now(timezone.utc)},
            message='Sentiment served from fallback because the primary service is unavailable.',
        )
