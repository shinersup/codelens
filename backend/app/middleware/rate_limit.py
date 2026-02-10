"""
Per-user rate limiting using Redis.
"""

from fastapi import HTTPException, status

from app.services.cache import redis_client


async def check_rate_limit(
    user_id: int,
    action: str,
    max_requests: int = 20,
    window_seconds: int = 3600,
) -> None:
    """
    Check if a user has exceeded their rate limit.

    Args:
        user_id: the user making the request
        action: which endpoint ("review", "explain", "refactor")
        max_requests: max allowed requests per window
        window_seconds: window duration in seconds (default 1 hour)

    Raises:
        HTTPException 429 if rate limit exceeded
    """
    key = f"ratelimit:{user_id}:{action}"

    try:
        current = await redis_client.get(key)

        if current and int(current) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {max_requests} {action}s per hour.",
            )

        # Increment counter and set TTL if it's a new key
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds)
        await pipe.execute()

    except HTTPException:
        raise  # re-raise our 429
    except Exception:
        # If Redis is down, allow the request (fail open)
        pass
