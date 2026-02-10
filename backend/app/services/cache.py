"""
Redis caching service.
"""

import json
import hashlib
from typing import Any

import redis.asyncio as redis

from app.config import settings

# Create Redis connection pool (reused across requests)
redis_client = redis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
)


def make_cache_key(prefix: str, code: str, language: str) -> str:
    """
    Create a deterministic cache key from code content.

    Same code + language always produces the same key.
    Use SHA-256 so the key is fixed-length regardless of code size.
    """
    content = f"{language}:{code}"
    hash_digest = hashlib.sha256(content.encode()).hexdigest()[:16]
    return f"{prefix}:{hash_digest}"


async def get_cached(key: str) -> dict | None:
    """
    Retrieve a cached result from Redis.

    Returns None if the key doesn't exist or has expired.
    """
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except redis.RedisError:
        # If Redis is down, just skip caching (don't crash the app)
        return None


async def set_cached(key: str, value: Any, ttl: int = 3600) -> None:
    """
    Store a result in Redis with a TTL.

    Args:
        key: the cache key
        value: any JSON-serializable data
        ttl: time to live in seconds (default: 1 hour)
    """
    try:
        await redis_client.set(key, json.dumps(value), ex=ttl)
    except redis.RedisError:
        # If Redis is down, just skip caching
        pass


async def check_redis_health() -> bool:
    """Check if Redis is reachable."""
    try:
        await redis_client.ping()
        return True
    except redis.RedisError:
        return False
