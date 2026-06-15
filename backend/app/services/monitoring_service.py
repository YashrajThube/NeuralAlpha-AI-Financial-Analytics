import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.logs import LogEntry
from app.db.models.prediction import Prediction
from app.schemas.monitoring import MonitoringData
from app.services.log_service import LogService


class MonitoringService:
    @staticmethod
    def _to_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    async def get_metrics(db: AsyncSession) -> MonitoringData:
        # Use DB-consistent naive timestamps for filtering and window comparisons.
        now_db = datetime.now()
        since_db = now_db - timedelta(hours=24)

        total_q = await db.execute(select(func.count(Prediction.id)).where(Prediction.created_at >= since_db))
        total = int(total_q.scalar_one() or 0)

        avg_conf_q = await db.execute(select(func.avg(Prediction.confidence)).where(Prediction.created_at >= since_db))
        avg_conf = float(avg_conf_q.scalar_one() or 0.0)

        usage_q = await db.execute(
            select(LogEntry.action, func.count(LogEntry.id))
            .where(LogEntry.timestamp >= since_db)
            .group_by(LogEntry.action)
        )
        usage_stats = {str(action): int(count) for action, count in usage_q.all()}

        inference_actions = {'prediction.request', 'forecast.request', 'chat.request'}
        logs_q = await db.execute(
            select(LogEntry.action, LogEntry.status, LogEntry.message, LogEntry.timestamp)
            .where(LogEntry.timestamp >= since_db)
            .where(LogEntry.action.in_(inference_actions))
        )
        logs = logs_q.all()
        inference_logs = logs

        if inference_logs:
            errors = sum(1 for row in inference_logs if row.status != 'success')
            error_rate = errors / len(inference_logs)
        else:
            error_rate = 0.0

        latencies = []
        for row in logs:
            if not row.message:
                continue
            try:
                payload = json.loads(row.message)
                latency = float(payload.get('latency_ms', 0.0))
                if latency > 0:
                    latencies.append(latency)
            except Exception:  # noqa: BLE001
                continue

        if latencies:
            latencies.sort()
            p95_idx = int(round(0.95 * (len(latencies) - 1)))
            p99_idx = int(round(0.99 * (len(latencies) - 1)))
            p95_latency_ms = float(latencies[p95_idx])
            p99_latency_ms = float(latencies[p99_idx])
            avg_latency_ms = float(sum(latencies) / len(latencies))
        else:
            p95_latency_ms = 0.0
            p99_latency_ms = 0.0
            avg_latency_ms = 0.0

        slo_window_start = now_db - timedelta(minutes=settings.monitoring_slo_window_minutes)
        recent_slo_latencies: list[float] = []
        recent_slo_total = 0
        recent_slo_errors = 0
        for row in logs:
            row_timestamp = row.timestamp if row.timestamp.tzinfo is None else row.timestamp.astimezone(timezone.utc).replace(tzinfo=None)
            if row_timestamp < slo_window_start:
                continue
            recent_slo_total += 1
            if row.status != 'success':
                recent_slo_errors += 1
            if not row.message:
                continue
            try:
                payload = json.loads(row.message)
                latency = float(payload.get('latency_ms', 0.0))
                if latency > 0:
                    recent_slo_latencies.append(latency)
            except Exception:  # noqa: BLE001
                continue

        if recent_slo_latencies:
            recent_slo_latencies.sort()
            recent_slo_p95 = float(recent_slo_latencies[int(round(0.95 * (len(recent_slo_latencies) - 1)))])
        else:
            recent_slo_p95 = p95_latency_ms

        recent_slo_error_rate = (recent_slo_errors / recent_slo_total) if recent_slo_total else error_rate

        chat_logs = [row for row in logs if row.action == 'chat.request']
        fallback_count = 0
        for row in chat_logs:
            if not row.message:
                continue
            try:
                payload = json.loads(row.message)
                if bool(payload.get('fallback_used', False)):
                    fallback_count += 1
            except Exception:  # noqa: BLE001
                continue
        fallback_rate = (fallback_count / len(chat_logs)) if chat_logs else 0.0

        recent_start = now_db - timedelta(hours=1)
        previous_start = now_db - timedelta(hours=2)
        recent_latencies: list[float] = []
        previous_latencies: list[float] = []
        for row in logs:
            if not row.message:
                continue
            try:
                payload = json.loads(row.message)
                latency = float(payload.get('latency_ms', 0.0))
            except Exception:  # noqa: BLE001
                continue
            if latency <= 0:
                continue
            row_timestamp = row.timestamp if row.timestamp.tzinfo is None else row.timestamp.astimezone(timezone.utc).replace(tzinfo=None)
            if row_timestamp >= recent_start:
                recent_latencies.append(latency)
            elif row_timestamp >= previous_start:
                previous_latencies.append(latency)

        recent_avg = (sum(recent_latencies) / len(recent_latencies)) if recent_latencies else 0.0
        previous_avg = (sum(previous_latencies) / len(previous_latencies)) if previous_latencies else 0.0
        anomaly_score = (recent_avg / previous_avg) if previous_avg > 0 else 0.0
        anomaly_detected = bool(previous_avg > 0 and anomaly_score >= settings.monitoring_anomaly_multiplier)

        slo_latency_breached = recent_slo_p95 > settings.monitoring_slo_latency_ms
        slo_error_breached = recent_slo_error_rate > settings.monitoring_slo_error_rate
        slo_breached = bool(slo_latency_breached or slo_error_breached)

        alerts: list[str] = []
        if slo_latency_breached:
            alerts.append(
                f'[critical] SLO latency breach: p95={round(recent_slo_p95, 2)}ms '
                f'target={round(settings.monitoring_slo_latency_ms, 2)}ms'
            )
        if slo_error_breached:
            alerts.append(
                f'[critical] SLO error breach: error_rate={round(recent_slo_error_rate, 4)} '
                f'target<={round(settings.monitoring_slo_error_rate, 4)}'
            )
        if p95_latency_ms > settings.monitoring_latency_alert_ms:
            alerts.append(f'[warning] High latency: p95={round(p95_latency_ms, 2)}ms')
        if error_rate > settings.monitoring_error_rate_alert:
            alerts.append(f'[warning] Error spike: error_rate={round(error_rate, 4)}')
        if settings.gemini_api_key.strip() and fallback_rate > settings.monitoring_fallback_alert:
            alerts.append(f'[warning] Gemini fallback elevated: rate={round(fallback_rate, 4)}')
        if anomaly_detected:
            alerts.append(f'[warning] Latency trend anomaly detected: score={round(anomaly_score, 3)}')

        if alerts:
            await LogService.create_log(
                db,
                action='monitoring.alert',
                status='warning' if not slo_breached else 'critical',
                message=json.dumps(
                    {
                        'alerts': alerts,
                        'slo_breached': slo_breached,
                        'p95_latency_ms': p95_latency_ms,
                        'slo_p95_latency_ms': recent_slo_p95,
                        'error_rate': error_rate,
                        'slo_error_rate': recent_slo_error_rate,
                        'fallback_rate': fallback_rate,
                        'anomaly_score': anomaly_score,
                    }
                ),
            )

        return MonitoringData(
            total_predictions_24h=total,
            avg_confidence_24h=round(avg_conf, 4),
            error_rate_24h=error_rate,
            avg_latency_ms_24h=round(avg_latency_ms, 3),
            p95_latency_ms=p95_latency_ms,
            p99_latency_ms=p99_latency_ms,
            gemini_fallback_rate_24h=fallback_rate,
            usage_stats_24h=usage_stats,
            alerts=alerts,
            anomaly_detected=anomaly_detected,
            anomaly_score=round(anomaly_score, 4),
            slo_p95_latency_ms=round(recent_slo_p95, 3),
            slo_error_rate=round(recent_slo_error_rate, 4),
            slo_latency_target_ms=settings.monitoring_slo_latency_ms,
            slo_error_rate_target=settings.monitoring_slo_error_rate,
            slo_latency_breached=slo_latency_breached,
            slo_error_breached=slo_error_breached,
            slo_breached=slo_breached,
        )
