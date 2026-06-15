from pydantic import BaseModel


class MonitoringData(BaseModel):
    total_predictions_24h: int
    avg_confidence_24h: float
    error_rate_24h: float
    avg_latency_ms_24h: float
    p95_latency_ms: float
    p99_latency_ms: float
    gemini_fallback_rate_24h: float
    usage_stats_24h: dict[str, int]
    alerts: list[str]
    anomaly_detected: bool
    anomaly_score: float
    slo_p95_latency_ms: float
    slo_error_rate: float
    slo_latency_target_ms: float
    slo_error_rate_target: float
    slo_latency_breached: bool
    slo_error_breached: bool
    slo_breached: bool
