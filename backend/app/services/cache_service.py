from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Callable
from typing import Any

from app.core.config import settings


class CacheService:
    _redis_client: Any = None
    _memory_store: dict[str, tuple[float, str]] = {}
    _lock = asyncio.Lock()

    @classmethod
    async def init(cls) -> None:
        if not settings.cache_enabled:
            return

        try:
            import redis.asyncio as redis

            cls._redis_client = redis.from_url(settings.redis_url, encoding='utf-8', decode_responses=True)
            await cls._redis_client.ping()
        except Exception:
            cls._redis_client = None

    @classmethod
    async def close(cls) -> None:
        if cls._redis_client is not None:
            try:
                await cls._redis_client.close()
            except Exception:
                pass
        cls._redis_client = None

    @classmethod
    async def get_json(cls, key: str) -> dict[str, Any] | None:
        if not settings.cache_enabled:
            return None

        if cls._redis_client is not None:
            try:
                raw = await cls._redis_client.get(key)
                if raw:
                    return json.loads(raw)
            except Exception:
                pass

        async with cls._lock:
            row = cls._memory_store.get(key)
            if not row:
                return None
            expires_at, payload = row
            if expires_at < time.time():
                cls._memory_store.pop(key, None)
                return None
            try:
                return json.loads(payload)
            except Exception:
                return None

    @classmethod
    async def set_json(cls, key: str, value: dict[str, Any], ttl_seconds: int | None = None) -> None:
        if not settings.cache_enabled:
            return

        ttl = int(ttl_seconds or settings.cache_ttl_seconds)
        payload = json.dumps(value)

        if cls._redis_client is not None:
            try:
                await cls._redis_client.set(key, payload, ex=ttl)
                return
            except Exception:
                pass

        async with cls._lock:
            cls._memory_store[key] = (time.time() + ttl, payload)

    @classmethod
    async def get_or_set_json(
        cls,
        key: str,
        producer: Callable[[], Any],
        ttl_seconds: int | None = None,
    ) -> dict[str, Any]:
        cached = await cls.get_json(key)
        if cached is not None:
            return cached

        value = producer()
        if asyncio.iscoroutine(value):
            value = await value
        if not isinstance(value, dict):
            raise TypeError('Cache producer must return a dict')
        await cls.set_json(key, value, ttl_seconds=ttl_seconds)
        return value
