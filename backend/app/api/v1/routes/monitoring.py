import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.services.monitoring_service import MonitoringService
from app.utils.helpers import success_response

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get('/monitoring', response_model=ApiResponse)
async def monitoring(
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    try:
        result = await MonitoringService.get_metrics(db)
        return success_response(result.model_dump())
    except Exception:
        logger.exception('monitoring_fallback')
        return success_response(
            {
                'total_predictions_24h': 0,
                'avg_confidence_24h': 0.0,
                'error_rate_24h': 0.0,
                'avg_latency_ms_24h': 0.0,
                'p95_latency_ms': 0.0,
                'p99_latency_ms': 0.0,
                'gemini_fallback_rate_24h': 0.0,
                'usage_stats_24h': {},
                'alerts': ['Monitoring storage unavailable; fallback metrics are active.'],
                'anomaly_detected': False,
                'anomaly_score': 0.0,
                'slo_p95_latency_ms': 0.0,
                'slo_error_rate': 0.0,
                'slo_latency_target_ms': settings.monitoring_slo_latency_ms,
                'slo_error_rate_target': settings.monitoring_slo_error_rate,
                'slo_latency_breached': False,
                'slo_error_breached': False,
                'slo_breached': False,
            },
            message='Monitoring served from fallback because the primary service is unavailable.',
        )
