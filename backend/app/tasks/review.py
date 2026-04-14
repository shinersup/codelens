"""
Celery tasks for LLM-powered code analysis.

Each task is a thin synchronous wrapper around the async LLM service methods.

Two problems solved here:

1. "Event loop is closed"
   asyncio.run() destroys the loop when it exits. If a second task runs in the
   same worker process, asyncio internal state (e.g. in redis-py's connection
   pool) still holds a reference to the old closed loop and raises. Fix:
   asyncio.new_event_loop() + loop.run_until_complete() + loop.close() gives a
   truly fresh loop every time with no shared state.

2. "cannot perform operation: another operation is in progress"
   app.db.SessionLocal is bound to a module-level engine whose connection pool
   was created in the original event loop. When a new loop runs a task, asyncpg
   connections from the old pool are invalid in the new loop context. Fix: each
   task creates its own engine (fresh pool, fresh event loop) and disposes it
   when done. The engine is local to the _inner() coroutine so it cannot be
   shared across concurrent tasks even if the worker runs multiple at once.
"""

import asyncio
import logging

from app.worker import celery_app
from app.config import settings

# Import ALL models at module level so SQLAlchemy's Base.metadata knows about
# every table — including 'users' — before any session is opened.
# Without this, foreign key resolution fails with:
#   "Foreign key associated with column 'reviews.user_id' could not find table 'users'"
import app.models.user          # noqa: F401
import app.models.review        # noqa: F401
import app.models.analytics     # noqa: F401
import app.models.feedback      # noqa: F401

logger = logging.getLogger(__name__)


def _run_sync(coro):
    """
    Run a coroutine in a brand-new event loop.

    asyncio.run() is NOT used here because it sets a global event loop policy
    state that can bleed into the next task invocation. new_event_loop() +
    run_until_complete() + explicit close() is fully self-contained.
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _make_session():
    """
    Create a fresh async engine + session scoped to a single task invocation.

    Returns (engine, session). Caller must await engine.dispose() after the
    session is closed to release the connection pool.

    We cannot reuse app.db.engine / SessionLocal because those objects were
    created in the FastAPI process's event loop. A Celery worker runs in a
    separate process with its own event loop; asyncpg connections are bound to
    the loop they were created in and will raise if used from a different one.
    """
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_size=1,        # one connection is enough per short-lived task
        max_overflow=0,
    )
    session = AsyncSession(engine, expire_on_commit=False)
    return engine, session


@celery_app.task(name="tasks.review_code", bind=True, max_retries=0)
def task_review_code(self, code: str, language: str, user_id: int) -> dict:
    """
    Run a code review in the background.

    Returns a dict matching ReviewResponse shape:
        {"review": {...}, "cached": bool, "review_id": int | None}
    """
    async def _inner():
        from app.services.llm import llm_service
        from app.models.review import Review as ReviewModel

        result, was_cached = await llm_service.review_code(code, language)

        review_id = None
        if not was_cached:
            engine, session = _make_session()
            try:
                async with session:
                    review = ReviewModel(
                        user_id=user_id,
                        code=code,
                        language=language,
                        review_type="review",
                        result=result.model_dump(),
                        score=result.score,
                    )
                    session.add(review)
                    await session.commit()
                    await session.refresh(review)
                    review_id = review.id
            finally:
                await engine.dispose()

        return {
            "review": result.model_dump(),
            "cached": was_cached,
            "review_id": review_id,
        }

    try:
        return _run_sync(_inner())
    except Exception as exc:
        logger.error("task_review_code failed: %s", exc)
        raise


@celery_app.task(name="tasks.explain_code", bind=True, max_retries=0)
def task_explain_code(self, code: str, language: str, user_id: int) -> dict:
    """
    Run a code explanation in the background.

    Returns: {"explanation": str, "cached": bool}
    """
    async def _inner():
        from app.services.llm import llm_service
        from app.models.review import Review as ReviewModel

        explanation, was_cached = await llm_service.explain_code(code, language)

        if not was_cached:
            engine, session = _make_session()
            try:
                async with session:
                    review = ReviewModel(
                        user_id=user_id,
                        code=code,
                        language=language,
                        review_type="explain",
                        result={"explanation": explanation},
                    )
                    session.add(review)
                    await session.commit()
            finally:
                await engine.dispose()

        return {"explanation": explanation, "cached": was_cached}

    try:
        return _run_sync(_inner())
    except Exception as exc:
        logger.error("task_explain_code failed: %s", exc)
        raise


@celery_app.task(name="tasks.suggest_refactor", bind=True, max_retries=0)
def task_suggest_refactor(self, code: str, language: str, user_id: int) -> dict:
    """
    Run a refactor analysis in the background.

    Returns: {"suggestions": str, "cached": bool}
    """
    async def _inner():
        from app.services.llm import llm_service
        from app.models.review import Review as ReviewModel

        suggestions, was_cached = await llm_service.suggest_refactor(code, language)

        if not was_cached:
            engine, session = _make_session()
            try:
                async with session:
                    review = ReviewModel(
                        user_id=user_id,
                        code=code,
                        language=language,
                        review_type="refactor",
                        result={"suggestions": suggestions},
                    )
                    session.add(review)
                    await session.commit()
            finally:
                await engine.dispose()

        return {"suggestions": suggestions, "cached": was_cached}

    try:
        return _run_sync(_inner())
    except Exception as exc:
        logger.error("task_suggest_refactor failed: %s", exc)
        raise
