"""
Feedback routes — let users mark which review suggestions they actually applied.

POST /api/history/{review_id}/feedback — upsert feedback for one issue (toggle applied/not)
GET  /api/history/{review_id}/feedback — get all feedback records for a review
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.feedback import IssueFeedback
from app.models.review import Review
from app.models.user import User
from app.schemas.feedback import FeedbackItem, FeedbackResponse, FeedbackUpsert
from app.services.auth import get_current_user

router = APIRouter(prefix="/api", tags=["feedback"])


async def _get_own_review(review_id: int, user: User, db: AsyncSession) -> Review:
    """Fetch a review that belongs to this user, or raise 404."""
    result = await db.execute(
        select(Review).where(Review.id == review_id, Review.user_id == user.id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return review


@router.post("/history/{review_id}/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    review_id: int,
    body: FeedbackUpsert,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upsert feedback for one issue in a review.

    Calling this twice for the same issue_index updates the existing record (toggle).
    Returns all feedback for the review after the upsert so the frontend can sync state.
    """
    await _get_own_review(review_id, user, db)

    # Select-then-update to stay DB-agnostic (no pg-specific ON CONFLICT needed)
    existing = (
        await db.execute(
            select(IssueFeedback).where(
                IssueFeedback.review_id == review_id,
                IssueFeedback.issue_index == body.issue_index,
                IssueFeedback.user_id == user.id,
            )
        )
    ).scalar_one_or_none()

    if existing:
        existing.applied = body.applied
        if body.category is not None:
            existing.category = body.category
    else:
        db.add(IssueFeedback(
            review_id=review_id,
            issue_index=body.issue_index,
            category=body.category,
            applied=body.applied,
            user_id=user.id,
        ))

    await db.flush()

    rows = (
        await db.execute(
            select(IssueFeedback).where(
                IssueFeedback.review_id == review_id,
                IssueFeedback.user_id == user.id,
            )
        )
    ).scalars().all()

    return FeedbackResponse(
        review_id=review_id,
        feedbacks=[FeedbackItem(issue_index=r.issue_index, applied=r.applied) for r in rows],
    )


@router.get("/history/{review_id}/feedback", response_model=FeedbackResponse)
async def get_feedback(
    review_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all feedback records for a review (to restore UI state on revisit)."""
    await _get_own_review(review_id, user, db)

    rows = (
        await db.execute(
            select(IssueFeedback).where(
                IssueFeedback.review_id == review_id,
                IssueFeedback.user_id == user.id,
            )
        )
    ).scalars().all()

    return FeedbackResponse(
        review_id=review_id,
        feedbacks=[FeedbackItem(issue_index=r.issue_index, applied=r.applied) for r in rows],
    )
