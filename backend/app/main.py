from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_v1_router
from app.api.legacy_routes import legacy_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.db.init_db import init_db
from app.db.session import engine
from app.middleware.api_key import APIKeyMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.services.cache_service import CacheService
from app.services.model_loader import validate_required_models, warmup_models


legacy_api_logger = logging.getLogger('app.legacy_api')
startup_logger = logging.getLogger('app.startup')


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    startup_logger.info(
        'startup_config environment=%s api_key_required=%s api_key_configured=%s cache_enabled=%s redis_url=%s database_url=%s',
        settings.environment,
        settings.api_key_required,
        settings.api_key_configured,
        settings.cache_enabled,
        settings.redis_url,
        settings.database_url,
    )
    try:
        await init_db()
        startup_logger.info('startup_database status=ready')
    except Exception:
        startup_logger.exception('startup_database status=unavailable')
        if not settings.is_local_environment:
            raise

    await CacheService.init()
    startup_logger.info('startup_cache status=ready')
    if settings.model_warmup_on_startup:
        warmup_models()
        startup_logger.info('startup_models status=warmup_complete')
    if settings.enforce_real_models:
        try:
            validate_required_models()
            startup_logger.info('startup_models status=validated')
        except Exception:
            startup_logger.exception('startup_models status=validation_failed')
            if not settings.is_local_environment:
                raise
    yield
    await CacheService.close()
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version='1.0.0',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['Content-Type', 'Accept', 'X-API-Key'],
)
app.add_middleware(APIKeyMiddleware)
app.add_middleware(RateLimitMiddleware)

register_exception_handlers(app)


@app.get('/health')
async def health() -> dict:
    return {'success': True, 'data': {'status': 'ok', 'env': settings.environment}, 'error': None, 'message': None}


@app.middleware('http')
async def log_legacy_api_usage(request: Request, call_next):
    path = request.url.path
    if path.startswith('/api/') and not path.startswith('/api/v1/'):
        legacy_api_logger.warning('legacy_api_used path=%s method=%s client=%s', path, request.method, request.client.host if request.client else 'unknown')
    return await call_next(request)


async def health_check() -> dict:
    return {'status': 'ok', 'env': settings.environment}


app.include_router(api_v1_router, prefix=settings.api_v1_prefix)
app.include_router(legacy_router, prefix='/api')
