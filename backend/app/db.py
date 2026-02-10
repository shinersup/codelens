"""
Database connection and session management.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# Create the async engine (connection pool to PostgreSQL)
# echo=True logs SQL queries in development — turn off in production
engine = create_async_engine(
    settings.database_url,
    echo=(settings.app_env == "development"),
    pool_size=20,          # max connections in the pool
    max_overflow=5,        # extra connections allowed during spikes
    pool_timeout=30,       # seconds to wait for a connection
)

# Session factory — each call creates a new session
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # don't expire objects after commit
)


# Base class for all database models
class Base(DeclarativeBase):
    pass


async def get_db():
    """
    FastAPI dependency that provides a database session per request.

    Usage in a route:
        @router.get("/something")
        async def my_route(db: AsyncSession = Depends(get_db)):
            ...

    The session is automatically closed when the request finishes.
    """
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
