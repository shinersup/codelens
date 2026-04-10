"""
RequestLog model — stores per-request telemetry for analytics.

Logged by AnalyticsMiddleware on every tracked endpoint call.
"""

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.db import Base


class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    endpoint = Column(String(100), nullable=False)       # "/api/review", "/api/explain", etc.
    method = Column(String(10), nullable=False)           # "POST", "GET"
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Float, nullable=False)      # wall-clock ms via time.perf_counter()
    was_cached = Column(Boolean, nullable=True)           # True/False/None for non-cacheable routes
    language = Column(String(50), nullable=True)          # from request body when available
    review_type = Column(String(20), nullable=True)       # "review", "explain", "refactor"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
