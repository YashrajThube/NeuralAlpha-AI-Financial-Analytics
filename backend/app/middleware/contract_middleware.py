from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware


class ObservabilityValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        return await call_next(request)