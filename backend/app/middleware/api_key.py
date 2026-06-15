from __future__ import annotations

import logging

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import settings


logger = logging.getLogger(__name__)


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Keep health/docs reachable without API key.
        if path in {'/health', '/docs', '/openapi.json', '/redoc'}:
            return await call_next(request)

        # Apply only to API routes.
        if not path.startswith('/api/'):
            return await call_next(request)

        if not settings.api_key_required:
            return await call_next(request)

        configured_key = settings.public_api_key.strip()
        if not configured_key:
            if settings.is_local_environment:
                logger.warning(
                    'api_key_protection_disabled reason=missing_public_api_key environment=%s',
                    settings.environment,
                )
                return await call_next(request)

            return JSONResponse(
                status_code=503,
                content={
                    'success': False,
                    'data': None,
                    'error': 'API key protection misconfigured',
                    'message': 'PUBLIC_API_KEY must be configured when API key protection is enabled.',
                },
            )

        provided_key = request.headers.get('X-API-Key', '').strip()
        if provided_key != configured_key:
            return JSONResponse(
                status_code=401,
                content={
                    'success': False,
                    'data': None,
                    'error': 'Unauthorized',
                    'message': 'Missing or invalid API key.',
                },
            )

        client_ip = request.client.host if request.client else 'unknown'
        allowed_ips = settings.api_key_allowed_ips
        if allowed_ips and client_ip not in allowed_ips:
            return JSONResponse(
                status_code=403,
                content={
                    'success': False,
                    'data': None,
                    'error': 'Forbidden',
                    'message': 'Client IP is not allowed for this API key.',
                },
            )

        return await call_next(request)
