"""
Redis caching service.

Two things happen here beyond simple get/set:

1. Structured logging — every hit, miss, and error is logged at the
   appropriate level so cache behavior is visible in application logs.

2. Redis increment counters — INCR on codelens:stats:cache_hits /
   cache_misses on every get_cached call. These are O(1) atomic operations
   that give real-time running totals without a database query. They
   complement the per-request rows written by AnalyticsMiddleware, which
   provide time-series data; the counters provide a fast live snapshot.
"""

import hashlib
import json
import logging
from typing import Any

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)

CACHE_HITS_KEY = "codelens:stats:cache_hits"
CACHE_MISSES_KEY = "codelens:stats:cache_misses"

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
    Increments hit/miss counters and logs the outcome.
    """
    try:
        data = await redis_client.get(key)
        if data:
            await redis_client.incr(CACHE_HITS_KEY)
            logger.debug("Cache hit: %s", key)
            return json.loads(data)

        await redis_client.incr(CACHE_MISSES_KEY)
        logger.debug("Cache miss: %s", key)
        return None
    except redis.RedisError as exc:
        logger.warning("Cache read failed for key %s: %s", key, exc)
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
        logger.debug("Cache set: %s (ttl=%ds)", key, ttl)
    except redis.RedisError as exc:
        logger.warning("Cache write failed for key %s: %s", key, exc)


async def get_cache_stats() -> dict[str, int]:
    """
    Return real-time hit/miss counters stored in Redis.

    These are running totals since the counters were last reset (or since
    Redis was first started). Unlike the request_logs table, which requires
    a DB query and gives time-series data, these counters are O(1) reads
    that reflect the live state of the cache layer.

    Returns {"hits": N, "misses": N} on success, or zeroes if Redis is down.
    """
    try:
        hits_raw, misses_raw = await redis_client.mget(CACHE_HITS_KEY, CACHE_MISSES_KEY)
        return {
            "hits": int(hits_raw or 0),
            "misses": int(misses_raw or 0),
        }
    except redis.RedisError as exc:
        logger.warning("Failed to read cache stats: %s", exc)
        return {"hits": 0, "misses": 0}


async def check_redis_health() -> bool:
    """Check if Redis is reachable."""
    try:
        await redis_client.ping()
        return True
    except redis.RedisError:
        return False
