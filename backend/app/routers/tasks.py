"""
Async task endpoints — decouple long-running LLM calls from HTTP connections.

POST /api/review/async    — submit a review job, returns 202 + task_id immediately
POST /api/explain/async   — submit an explain job
POST /api/refactor/async  — submit a refactor job
GET  /api/tasks/{task_id} — poll job status and retrieve result when complete

Design:
  - The three POST endpoints mirror the synchronous equivalents but return 202
    instead of blocking until the LLM responds (3-8 seconds).
  - Rate limiting is identical to the sync endpoints.
  - The GET endpoint queries Celery's Redis result backend. It requires auth
    but cannot verify ownership of the task_id (UUIDs are hard to guess —
    acceptable for a demo project; production would store task_id → user_id in DB).

Task state machine (Celery):
    PENDING  → task queued, worker hasn't picked it up yet
    STARTED  → worker is executing (requires task_track_started=True in worker config)
    SUCCESS  → result available via result.get()
    FAILURE  → task raised an exception; error message in result.result
"""

from fastapi import APIRouter, Depends, status

from app.models.user import User
from app.schemas.review import ReviewRequest
from app.services.auth import get_current_user
from app.middleware.rate_limit import check_rate_limit

router = APIRouter(prefix="/api", tags=["tasks"])

# Map Celery states to client-friendly status strings
_STATE_MAP = {
    "PENDING": "pending",
    "STARTED": "processing",
    "SUCCESS": "complete",
    "FAILURE": "failed",
}


@router.post("/review/async", status_code=status.HTTP_202_ACCEPTED)
async def review_code_async(
    request: ReviewRequest,
    user: User = Depends(get_current_user),
):
    """
    Submit a code review as a background task.

    Returns immediately with a task_id. Poll GET /api/tasks/{task_id} for status.
    """
    from app.tasks.review import task_review_code

    await check_rate_limit(user.id, "review", max_requests=10000)
    task = task_review_code.delay(request.code, request.language, user.id)
    return {"task_id": task.id}


@router.post("/explain/async", status_code=status.HTTP_202_ACCEPTED)
async def explain_code_async(
    request: ReviewRequest,
    user: User = Depends(get_current_user),
):
    """Submit a code explanation as a background task."""
    from app.tasks.review import task_explain_code

    await check_rate_limit(user.id, "explain", max_requests=10000)
    task = task_explain_code.delay(request.code, request.language, user.id)
    return {"task_id": task.id}


@router.post("/refactor/async", status_code=status.HTTP_202_ACCEPTED)
async def suggest_refactor_async(
    request: ReviewRequest,
    user: User = Depends(get_current_user),
):
    """Submit a refactor analysis as a background task."""
    from app.tasks.review import task_suggest_refactor

    await check_rate_limit(user.id, "refactor", max_requests=10000)
    task = task_suggest_refactor.delay(request.code, request.language, user.id)
    return {"task_id": task.id}


@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    _user: User = Depends(get_current_user),
):
    """
    Poll the status of a background task.

    Response shape:
        {"status": "pending|processing|complete|failed", "result": <payload|null>}

    When status == "complete", `result` contains the same payload as the
    equivalent synchronous endpoint (e.g. ReviewResponse for review tasks).
    When status == "failed", `result` contains {"error": "<message>"}.
    """
    from celery.result import AsyncResult
    from app.worker import celery_app

    ar = AsyncResult(task_id, app=celery_app)
    state = ar.state  # PENDING / STARTED / SUCCESS / FAILURE / REVOKED / …

    client_status = _STATE_MAP.get(state, state.lower())

    if state == "SUCCESS":
        return {"status": client_status, "result": ar.result}

    if state == "FAILURE":
        return {
            "status": client_status,
            "result": {"error": str(ar.result)},
        }

    return {"status": client_status, "result": None}
