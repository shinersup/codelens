"""
IssueFeedback model — records whether a user applied a specific code review suggestion.

Each row tracks one issue (by its index in the review's issue list) and whether the
developer actually applied the suggestion. Unique on (review_id, issue_index) so a user
can toggle applied/not-applied without creating duplicates.

The 'category' column is denormalized from the review result at write time so that
analytics queries (e.g. application rate by category) don't need to scan result JSON.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from app.db import Base


class IssueFeedback(Base):
    __tablename__ = "issue_feedback"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(
        Integer,
        ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    issue_index = Column(Integer, nullable=False)
    category = Column(String(50), nullable=True)   # denormalized: bug/security/performance/style
    applied = Column(Boolean, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("review_id", "issue_index", name="uq_feedback_review_issue"),
    )
