"""
Response schema for GET /api/analytics.
"""

from pydantic import BaseModel


class LatencyStats(BaseModel):
    cached_ms: float | None
    uncached_ms: float | None


class FeedbackStats(BaseModel):
    total_feedback: int                    # total issue feedback records submitted
    applied_count: int                     # how many were marked as applied
    application_rate: float | None         # applied_count / total_feedback; None if no feedback yet
    applied_by_category: dict[str, int]    # {"security": N, "bug": N, ...} — applied suggestions


class AnalyticsResponse(BaseModel):
    total_requests: int
    cache_hit_rate: float | None           # 0.0–1.0, None if no cacheable requests yet
    avg_latency_ms: LatencyStats
    score_distribution: dict[str, int]     # {"1-3": N, "4-6": N, "7-9": N, "10": N}
    issue_category_breakdown: dict[str, int]
    requests_by_type: dict[str, int]
    live_cache_counts: dict[str, int]      # {"hits": N, "misses": N} — live Redis counters
    feedback: FeedbackStats                # user feedback on suggestion actionability
