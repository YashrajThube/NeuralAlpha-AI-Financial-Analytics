from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import settings


class InMemoryRateLimiter(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._windows: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get('content-length')
        if content_length and int(content_length) > settings.max_request_body_bytes:
            return JSONResponse(
                status_code=413,
                content={
                    'success': False,
                    'data': None,
                    'error': 'Request body too large',
                    'message': f'Max allowed size is {settings.max_request_body_bytes} bytes',
                },
            )

        client_ip = request.client.host if request.client else 'unknown'
        now = time.time()
        window = settings.rate_limit_window_seconds
        max_hits = settings.rate_limit_per_window

        bucket = self._windows[client_ip]
        while bucket and (now - bucket[0]) > window:
            bucket.popleft()

        if len(bucket) >= max_hits:
            return JSONResponse(
                status_code=429,
                content={
                    'success': False,
                    'data': None,
                    'error': 'Rate limit exceeded',
                    'message': f'Exceeded {max_hits} requests per {window}s',
                },
                headers={'Retry-After': str(window)},
            )

        bucket.append(now)
        return await call_next(request)


class RateLimitMiddleware(InMemoryRateLimiter):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in {'/docs', '/openapi.json'}:
            return await call_next(request)
        return await super().dispatch(request, call_next)
