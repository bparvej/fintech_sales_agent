"""
Async Redis cache client.

Provides caching for crawl results, search results, and LLM responses.
"""

from __future__ import annotations

import json
from typing import Any, Optional

import redis.asyncio as redis

from app.shared.config.settings import get_settings
from app.shared.logging.logger import get_logger

logger = get_logger(__name__)


class RedisCache:
    """Async Redis cache wrapper with JSON serialization."""

    def __init__(self) -> None:
        self._client: Optional[redis.Redis] = None

    async def initialize(self) -> None:
        """Initialize the Redis connection."""
        settings = get_settings()
        self._client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        try:
            await self._client.ping()
            logger.info("Redis connection established")
        except redis.ConnectionError:
            logger.warning("Redis not available — caching disabled")
            self._client = None

    async def close(self) -> None:
        """Close the Redis connection."""
        if self._client:
            await self._client.close()
            logger.info("Redis connection closed")

    async def get(self, key: str) -> Optional[Any]:
        """Get a cached value by key."""
        if not self._client:
            return None
        try:
            value = await self._client.get(key)
            if value:
                return json.loads(value)
        except Exception as exc:
            logger.warning("Cache get failed", key=key, error=str(exc))
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 3600,
    ) -> bool:
        """Set a cached value with TTL."""
        if not self._client:
            return False
        try:
            serialized = json.dumps(value, default=str)
            await self._client.setex(key, ttl_seconds, serialized)
            return True
        except Exception as exc:
            logger.warning("Cache set failed", key=key, error=str(exc))
            return False

    async def delete(self, key: str) -> bool:
        """Delete a cached value."""
        if not self._client:
            return False
        try:
            await self._client.delete(key)
            return True
        except Exception as exc:
            logger.warning("Cache delete failed", key=key, error=str(exc))
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        if not self._client:
            return False
        try:
            return bool(await self._client.exists(key))
        except Exception:
            return False


# Global singleton
cache = RedisCache()
