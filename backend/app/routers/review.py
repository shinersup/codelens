"""
Review routes — the three LLM-powered endpoints plus history.

POST /api/review   — AI code review (structured bugs/security/perf analysis)
POST /api/explain  — AI code explanation (plain English)
POST /api/refactor — AI refactor suggestions (before/after examples)
GET  /api/history  — user's past reviews
GET  /api/history/{review_id} — full detail for a single past review
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.user import User
from app.models.review import Review
from app.schemas.review import (
    ReviewRequest,
    ReviewResponse,
    ExplainResponse,
    RefactorResponse,
    HistoryItem,
    HistoryPage,
    HistoryDetail,
)
from app.services.llm import llm_service
from app.services.auth import get_current_user
from app.middleware.rate_limit import check_rate_limit

router = APIRouter(prefix="/api", tags=["review"])


@router.post("/review", response_model=ReviewResponse)
async def review_code(
    http_request: Request,
    request: ReviewRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    AI-powered code review.
    """
    # Rate limit check
    await check_rate_limit(user.id, "review", max_requests=20)

    # Call LLM
    result, was_cached = await llm_service.review_code(request.code, request.language)

    # Populate state for AnalyticsMiddleware
    http_request.state.was_cached = was_cached
    http_request.state.language = request.language
    http_request.state.review_type = "review"

    # Save to history (don't save if it was a cache hit to avoid duplicates)
    review_id = None
    if not was_cached:
        review = Review(
            user_id=user.id,
            code=request.code,
            language=request.language,
            review_type="review",
            result=result.model_dump(),
            score=result.score,
        )
        db.add(review)
        await db.flush()
        review_id = review.id

    return ReviewResponse(review=result, cached=was_cached, review_id=review_id)


@router.post("/explain", response_model=ExplainResponse)
async def explain_code(
    http_request: Request,
    request: ReviewRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI-powered code explanation."""
    await check_rate_limit(user.id, "explain", max_requests=30)

    explanation, was_cached = await llm_service.explain_code(
        request.code, request.language
    )

    # Populate state for AnalyticsMiddleware
    http_request.state.was_cached = was_cached
    http_request.state.language = request.language
    http_request.state.review_type = "explain"

    if not was_cached:
        review = Review(
            user_id=user.id,
            code=request.code,
            language=request.language,
            review_type="explain",
            result={"explanation": explanation},
        )
        db.add(review)

    return ExplainResponse(explanation=explanation, cached=was_cached)


@router.post("/refactor", response_model=RefactorResponse)
async def suggest_refactor(
    http_request: Request,
    request: ReviewRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI-powered refactoring suggestions."""
    await check_rate_limit(user.id, "refactor", max_requests=20)

    suggestions, was_cached = await llm_service.suggest_refactor(
        request.code, request.language
    )

    # Populate state for AnalyticsMiddleware
    http_request.state.was_cached = was_cached
    http_request.state.language = request.language
    http_request.state.review_type = "refactor"

    if not was_cached:
        review = Review(
            user_id=user.id,
            code=request.code,
            language=request.language,
            review_type="refactor",
            result={"suggestions": suggestions},
        )
        db.add(review)

    return RefactorResponse(suggestions=suggestions, cached=was_cached)


_MAX_LIMIT = 50

@router.get("/history", response_model=HistoryPage)
async def get_history(
    after_id: int | None = Query(default=None, description="Return items with id < after_id (cursor)"),
    limit: int = Query(default=20, ge=1, le=_MAX_LIMIT, description="Number of items to return"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the current user's review history, most recent first.

    Cursor-based pagination via `after_id` + `limit`.
    Pass the returned `next_cursor` as `after_id` on the next request.
    `next_cursor` is None when there are no more results.
    """
    query = (
        select(Review)
        .where(Review.user_id == user.id)
        .order_by(Review.id.desc())
    )
    if after_id is not None:
        query = query.where(Review.id < after_id)

    # Fetch one extra row to determine whether another page exists
    result = await db.execute(query.limit(limit + 1))
    rows = result.scalars().all()

    has_more = len(rows) > limit
    page_rows = rows[:limit]

    items = [
        HistoryItem(
            id=r.id,
            language=r.language,
            review_type=r.review_type,
            score=r.score,
            created_at=r.created_at.isoformat(),
        )
        for r in page_rows
    ]

    return HistoryPage(
        items=items,
        next_cursor=page_rows[-1].id if has_more else None,
    )


@router.get("/history/{review_id}", response_model=HistoryDetail)
async def get_history_detail(
    review_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the full detail of a single past review."""
    result = await db.execute(
        select(Review).where(Review.id == review_id, Review.user_id == user.id)
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    return HistoryDetail(
        id=review.id,
        code=review.code,
        language=review.language,
        review_type=review.review_type,
        result=review.result,
        score=review.score,
        created_at=review.created_at.isoformat(),
    )

@router.delete("/history/{review_id}", status_code=204)
async def delete_history_item(
    review_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a single review from history."""
    result = await db.execute(
        select(Review).where(Review.id == review_id, Review.user_id == user.id)
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    await db.delete(review)


@router.delete("/history", status_code=204)
async def clear_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete all reviews for the current user."""
    result = await db.execute(
        select(Review).where(Review.user_id == user.id)
    )
    reviews = result.scalars().all()

    for review in reviews:
        await db.delete(review)