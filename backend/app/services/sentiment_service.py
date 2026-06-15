from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.sentiment import SentimentData
from app.schemas.sentiment import SentimentDataResponse
from app.services.cache_service import CacheService
from app.services.data_quality_service import DataQualityService
from app.services.log_service import LogService


def _label(score: float) -> str:
    if score > 0.1:
        return 'Positive'
    if score < -0.1:
        return 'Negative'
    return 'Neutral'


class SentimentService:
    @staticmethod
    async def analyze(symbol: str, db: AsyncSession) -> SentimentDataResponse:
        clean_symbol = symbol.upper().strip()
        cache_key = f"sentiment:{clean_symbol}"
        cached = await CacheService.get_json(cache_key)
        if cached:
            await LogService.create_log(
                db,
                user_id=None,
                action='sentiment.cache_hit',
                status='success',
                message=clean_symbol,
            )
            return SentimentDataResponse.model_validate(cached)

        score = round(((sum(ord(c) for c in clean_symbol) % 200) - 100) / 400, 4)
        label = _label(score)
        score, label = DataQualityService.sanitize_sentiment(score, label)

        row = SentimentData(
            symbol=clean_symbol,
            legacy_score=score,
            sentiment_score=score,
            sentiment_label=label,
            source='deterministic-v1',
            timestamp=datetime.now(timezone.utc),
        )
        db.add(row)
        flush = getattr(db, 'flush', None)
        if callable(flush):
            await flush()
        refresh = getattr(db, 'refresh', None)
        if callable(refresh):
            await refresh(row)

        await LogService.create_log(
            db,
            user_id=None,
            action='sentiment.analyze',
            status='success',
            message=f'{clean_symbol}:{score}',
        )

        response = SentimentDataResponse(
            symbol=row.symbol,
            score=row.sentiment_score,
            label=row.sentiment_label,
            timestamp=row.timestamp,
        )
        await CacheService.set_json(cache_key, response.model_dump(mode='json'), ttl_seconds=180)
        return response
