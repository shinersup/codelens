"""
Review model — stores every AI code review result.

The 'result' column stores the full LLM response as JSON,
so we can display it later without re-calling the API.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func

from app.db import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    code = Column(Text, nullable=False)
    language = Column(String(50), nullable=False)
    review_type = Column(String(20), nullable=False)  # "review", "explain", "refactor"
    result = Column(JSON, nullable=False)
    score = Column(Integer, nullable=True)  # code quality score 1-10 (only for "review" type)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
