"""
Analytics middleware — records per-request telemetry to the request_logs table.

Flow:
  1. Before calling next: record start time, initialize request.state slots.
  2. Route handlers populate request.state.was_cached / .language / .review_type.
  3. After calling next: compute elapsed ms, decode user_id from JWT, persist log.

Only the three LLM endpoints are tracked; all other paths pass through silently.
Failures are caught and logged — the middleware never breaks a live request.
"""

import logging
import time

from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import settings
from app.db import SessionLocal
from app.models.analytics import RequestLog

logger = logging.getLogger(__name__)

TRACKED_PATHS = {"/api/review", "/api/explain", "/api/refactor"}


class AnalyticsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Initialize state so route handlers can populate it without AttributeError
        request.state.was_cached = None
        request.state.language = None
        request.state.review_type = None

        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        if request.url.path in TRACKED_PATHS:
            user_id = _extract_user_id(request)
            await _persist_log(
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                response_time_ms=elapsed_ms,
                user_id=user_id,
                was_cached=getattr(request.state, "was_cached", None),
                language=getattr(request.state, "language", None),
                review_type=getattr(request.state, "review_type", None),
            )

        return response


def _extract_user_id(request: Request) -> int | None:
    """Decode user_id from the Authorization: Bearer <token> header. Never raises."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:]
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        sub = payload.get("sub")
        return int(sub) if sub else None
    except (JWTError, ValueError):
        return None


async def _persist_log(**kwargs) -> None:
    """Write a RequestLog row. Swallows all exceptions — analytics must not crash requests."""
    try:
        async with SessionLocal() as session:
            session.add(RequestLog(**kwargs))
            await session.commit()
    except Exception:
        logger.exception("AnalyticsMiddleware: failed to persist request log")
