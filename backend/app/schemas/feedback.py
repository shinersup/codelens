"""
Feedback schemas — for marking individual review suggestions as applied.
"""

from pydantic import BaseModel, Field


class FeedbackUpsert(BaseModel):
    """Body for POST /api/history/{review_id}/feedback."""
    issue_index: int = Field(..., ge=0)
    applied: bool
    category: str | None = None    # passed by the frontend from the issue object


class FeedbackItem(BaseModel):
    issue_index: int
    applied: bool

    class Config:
        from_attributes = True


class FeedbackResponse(BaseModel):
    review_id: int
    feedbacks: list[FeedbackItem]
