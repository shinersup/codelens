"""
Main FastAPI application.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import engine, Base
from app.routers import auth, review
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

# Register routes
app.include_router(auth.router)
app.include_router(review.router)


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
