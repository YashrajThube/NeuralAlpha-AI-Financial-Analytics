import asyncio
import json
import time

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.market_data import MarketData
from app.schemas.forecast import ForecastData, ForecastRequest
from app.services.cache_service import CacheService
from app.services.data_quality_service import DataQualityService
from app.services.log_service import LogService
from app.services.model_loader import get_model


class ForecastService:
    @staticmethod
    async def forecast(payload: ForecastRequest, db: AsyncSession) -> ForecastData:
        started = time.perf_counter()
        symbol = payload.symbol.upper()
        cache_key = f"forecast:{symbol}:{payload.horizon_days}"
        cached = await CacheService.get_json(cache_key)
        if cached:
            await LogService.create_log(
                db,
                action='forecast.cache_hit',
                status='success',
                message=json.dumps({'symbol': symbol, 'horizon_days': payload.horizon_days}),
            )
            return ForecastData.model_validate(cached)

        rows = await db.execute(
            select(MarketData.close)
            .where(MarketData.symbol == symbol)
            .order_by(MarketData.timestamp.desc())
            .limit(120)
        )
        closes = [float(value) for value in rows.scalars().all()]
        closes.reverse()
        lstm_model, lstm_version = get_model('lstm_model.keras')
        scaler, _ = get_model('scaler.pkl')
        model_version = lstm_version

        if lstm_model is not None and scaler is not None and len(closes) >= 60:
            window = np.asarray(closes[-60:], dtype=np.float32).reshape(-1, 1)
            scaled = np.asarray(scaler.transform(window), dtype=np.float32).reshape(-1)
            model_input = scaled.reshape(1, scaled.shape[0], 1)
            scaled_next = await asyncio.to_thread(
                lambda: float(np.asarray(lstm_model.predict(model_input, verbose=0), dtype=np.float32).reshape(-1)[0])
            )
            first_value = float(scaler.inverse_transform(np.asarray([[scaled_next]], dtype=np.float32))[0, 0])

            returns = np.diff(np.asarray(closes[-30:], dtype=np.float32)) / np.asarray(closes[-31:-1], dtype=np.float32)
            drift = float(np.clip(np.mean(returns), -0.04, 0.04)) if len(returns) else 0.0
            forecast_values = [round(first_value, 4)]
            current = first_value
            for _ in range(max(payload.horizon_days - 1, 0)):
                current *= 1.0 + drift
                forecast_values.append(round(current, 4))
        elif len(closes) < 2:
            baseline = closes[-1] if closes else 100.0
            forecast_values = [round(float(baseline), 4) for _ in range(payload.horizon_days)]
            model_version = f"{model_version}:baseline"
        else:
            returns = np.diff(np.asarray(closes, dtype=np.float32)) / np.asarray(closes[:-1], dtype=np.float32)
            drift = float(np.clip(np.mean(returns), -0.05, 0.05))
            current = float(closes[-1])
            forecast_values = []
            for _ in range(payload.horizon_days):
                current *= 1.0 + drift
                forecast_values.append(round(current, 4))
            model_version = f"{model_version}:stat-fallback"

        forecast_values = DataQualityService.sanitize_forecast(forecast_values)

        latency_ms = round((time.perf_counter() - started) * 1000, 3)
        await LogService.create_log(
            db,
            action='forecast.request',
            status='success',
            message=json.dumps(
                {
                    'symbol': symbol,
                    'latency_ms': latency_ms,
                    'points': len(forecast_values),
                    'model_version': model_version,
                }
            ),
        )

        response = ForecastData(symbol=symbol, horizon_days=payload.horizon_days, forecast=forecast_values)
        await CacheService.set_json(cache_key, response.model_dump(mode='json'), ttl_seconds=120)
        return response
