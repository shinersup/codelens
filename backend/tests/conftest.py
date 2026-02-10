"""
Test configuration and shared fixtures.
"""

import sys
import os

# Backend/ on the path so `import app` works
_backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

# Also handle Docker where WORKDIR is /app
if "/app" not in sys.path and os.path.isdir("/app/app"):
    sys.path.insert(0, "/app")

import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock()
    return db


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac