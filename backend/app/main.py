"""
Main FastAPI application.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import engine, Base
from app.middleware.analytics import AnalyticsMiddleware
from app.models import analytics as _analytics_models  # noqa: F401 — ensures table is registered with Base
from app.routers import auth, review
from app.routers import analytics
from app.services.cache import check_redis_health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on startup and shutdown.
    """
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


# Create the app
app = FastAPI(
    title="CodeLens API",
    description="AI-powered code review assistant",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the React frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Analytics middleware — must be added after CORS so it runs inside the CORS wrapper
app.add_middleware(AnalyticsMiddleware)

# Register routes
app.include_router(auth.router)
app.include_router(review.router)
app.include_router(analytics.router)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns the status of the API and its dependencies (Redis, DB).
    Useful for Docker health checks and monitoring.
    """
    redis_ok = await check_redis_health()
    return {
        "status": "healthy",
        "redis": "connected" if redis_ok else "disconnected",
    }
