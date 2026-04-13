"""
Analytics router.

GET /api/analytics — aggregate platform metrics derived from request_logs and reviews.

Requires authentication (any logged-in user). Returns platform-wide aggregates,
not per-user data, so this is safe to show in a demo without leaking PII.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.analytics import RequestLog
from app.models.feedback import IssueFeedback
from app.models.review import Review
from app.models.user import User
from app.schemas.analytics import AnalyticsResponse, FeedbackStats, LatencyStats
from app.services.auth import get_current_user
from app.services.cache import get_cache_stats

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return aggregate metrics across all tracked requests.

    Metrics:
    - total_requests: count of all logged LLM endpoint calls
    - cache_hit_rate: fraction of cacheable requests served from Redis
    - avg_latency_ms: mean wall-clock ms split by cached vs uncached
    - score_distribution: buckets of code quality scores from review runs
    - issue_category_breakdown: issue counts by category across all reviews
    - requests_by_type: call volume per review_type
    """

    # --- total requests ---
    total = (await db.execute(select(func.count()).select_from(RequestLog))).scalar() or 0

    # --- cache hit rate ---
    cacheable = (
        await db.execute(
            select(func.count())
            .select_from(RequestLog)
            .where(RequestLog.was_cached.isnot(None))
        )
    ).scalar() or 0

    hits = (
        await db.execute(
            select(func.count())
            .select_from(RequestLog)
            .where(RequestLog.was_cached.is_(True))
        )
    ).scalar() or 0

    cache_hit_rate = round(hits / cacheable, 3) if cacheable > 0 else None

    # --- avg latency: cached vs uncached ---
    cached_avg = (
        await db.execute(
            select(func.avg(RequestLog.response_time_ms)).where(
                RequestLog.was_cached.is_(True)
            )
        )
    ).scalar()

    uncached_avg = (
        await db.execute(
            select(func.avg(RequestLog.response_time_ms)).where(
                RequestLog.was_cached.is_(False)
            )
        )
    ).scalar()

    # --- score distribution (reviews table) ---
    scores = (
        await db.execute(
            select(Review.score).where(
                Review.review_type == "review",
                Review.score.isnot(None),
            )
        )
    ).scalars().all()

    score_dist: dict[str, int] = {"1-3": 0, "4-6": 0, "7-9": 0, "10": 0}
    for s in scores:
        if s <= 3:
            score_dist["1-3"] += 1
        elif s <= 6:
            score_dist["4-6"] += 1
        elif s < 10:
            score_dist["7-9"] += 1
        else:
            score_dist["10"] += 1

    # --- issue category breakdown (scan result JSON from all review runs) ---
    review_results = (
        await db.execute(select(Review.result).where(Review.review_type == "review"))
    ).scalars().all()

    category_counts: dict[str, int] = {}
    for result in review_results:
        if not isinstance(result, dict):
            continue
        for issue in result.get("issues", []):
            cat = issue.get("category", "unknown")
            category_counts[cat] = category_counts.get(cat, 0) + 1

    # --- requests by review_type ---
    type_rows = (
        await db.execute(
            select(RequestLog.review_type, func.count())
            .where(RequestLog.review_type.isnot(None))
            .group_by(RequestLog.review_type)
        )
    ).all()
    requests_by_type = {row[0]: row[1] for row in type_rows}

    # --- live Redis counters (real-time, no DB query) ---
    live_cache_counts = await get_cache_stats()

    # --- feedback stats ---
    total_fb = (
        await db.execute(select(func.count()).select_from(IssueFeedback))
    ).scalar() or 0

    applied_count = (
        await db.execute(
            select(func.count())
            .select_from(IssueFeedback)
            .where(IssueFeedback.applied.is_(True))
        )
    ).scalar() or 0

    application_rate = round(applied_count / total_fb, 3) if total_fb > 0 else None

    fb_by_cat_rows = (
        await db.execute(
            select(IssueFeedback.category, func.count())
            .where(
                IssueFeedback.applied.is_(True),
                IssueFeedback.category.isnot(None),
            )
            .group_by(IssueFeedback.category)
        )
    ).all()
    applied_by_category = {row[0]: row[1] for row in fb_by_cat_rows}

    return AnalyticsResponse(
        total_requests=total,
        cache_hit_rate=cache_hit_rate,
        avg_latency_ms=LatencyStats(
            cached_ms=round(cached_avg, 1) if cached_avg is not None else None,
            uncached_ms=round(uncached_avg, 1) if uncached_avg is not None else None,
        ),
        score_distribution=score_dist,
        issue_category_breakdown=category_counts,
        requests_by_type=requests_by_type,
        live_cache_counts=live_cache_counts,
        feedback=FeedbackStats(
            total_feedback=total_fb,
            applied_count=applied_count,
            application_rate=application_rate,
            applied_by_category=applied_by_category,
        ),
    )
