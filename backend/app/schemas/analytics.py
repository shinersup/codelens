"""
Response schema for GET /api/analytics.
"""

from pydantic import BaseModel


class LatencyStats(BaseModel):
    cached_ms: float | None
    uncached_ms: float | None


class AnalyticsResponse(BaseModel):
    total_requests: int
    cache_hit_rate: float | None           # 0.0–1.0, None if no cacheable requests yet
    avg_latency_ms: LatencyStats
    score_distribution: dict[str, int]     # {"1-3": N, "4-6": N, "7-9": N, "10": N}
    issue_category_breakdown: dict[str, int]
    requests_by_type: dict[str, int]
    live_cache_counts: dict[str, int]      # {"hits": N, "misses": N} — live Redis counters
