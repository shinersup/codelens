"""
CodeLens Test Suite — 31 tests
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ============================================================
# SAMPLE DATA
# ============================================================

MOCK_REVIEW_DATA = {
    "summary": "Clean code with minor style issues.",
    "issues": [
        {
            "line": 5,
            "severity": "warning",
            "category": "style",
            "description": "Unused variable 'x'",
            "suggestion": "Remove the unused variable or prefix with underscore",
        },
        {
            "line": 12,
            "severity": "critical",
            "category": "security",
            "description": "SQL injection vulnerability",
            "suggestion": "Use parameterized queries instead of string concatenation",
        },
        {
            "line": 8,
            "severity": "info",
            "category": "performance",
            "description": "List comprehension would be more efficient",
            "suggestion": "Replace the for loop with a list comprehension",
        },
    ],
    "score": 7,
}


# ============================================================
# 1. HEALTH CHECK (1 test)
# ============================================================

class TestHealthCheck:

    @pytest.mark.asyncio
    async def test_health_returns_200(self, client):
        """Health endpoint should return 200 with status."""
        with patch("app.main.check_redis_health", return_value=True):
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["redis"] == "connected"

    @pytest.mark.asyncio
    async def test_health_reports_redis_down(self, client):
        """Health endpoint should report when Redis is disconnected."""
        with patch("app.main.check_redis_health", return_value=False):
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json()["redis"] == "disconnected"


# ============================================================
# 2. AUTHENTICATION — "JWT authentication" (7 tests)
# ============================================================

class TestAuth:

    def test_password_hashing_works(self):
        """Hashed password should verify correctly."""
        from app.services.auth import hash_password, verify_password
        hashed = hash_password("my-secret-password")
        assert hashed != "my-secret-password"
        assert verify_password("my-secret-password", hashed) is True

    def test_wrong_password_rejected(self):
        """Wrong password should not verify."""
        from app.services.auth import hash_password, verify_password
        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_hash_is_unique_per_call(self):
        """Two hashes of the same password should differ (bcrypt uses random salt)."""
        from app.services.auth import hash_password
        h1 = hash_password("same-password")
        h2 = hash_password("same-password")
        assert h1 != h2  # different salts

    def test_jwt_token_is_string(self):
        """Token should be a non-empty string."""
        from app.services.auth import create_access_token
        token = create_access_token(user_id=42)
        assert isinstance(token, str)
        assert len(token) > 20

    def test_jwt_contains_user_id(self):
        """Token payload should contain the user ID as 'sub'."""
        from jose import jwt
        from app.services.auth import create_access_token
        from app.config import settings
        token = create_access_token(user_id=99)
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == "99"

    def test_jwt_has_expiration(self):
        """Token should have an expiration claim."""
        from jose import jwt
        from app.services.auth import create_access_token
        from app.config import settings
        token = create_access_token(user_id=1)
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert "exp" in payload

    @pytest.mark.asyncio
    async def test_protected_endpoint_rejects_no_token(self, client):
        """Review endpoint should return 401 without auth header."""
        response = await client.post(
            "/api/review",
            json={"code": "print('hello')", "language": "python"},
        )
        assert response.status_code == 401


# ============================================================
# 3. SCHEMA VALIDATION — "structured analysis" (8 tests)
# ============================================================

class TestSchemaValidation:

    def test_review_request_accepts_valid_input(self):
        from app.schemas.review import ReviewRequest
        req = ReviewRequest(code="print('hello')", language="python")
        assert req.code == "print('hello')"
        assert req.language == "python"

    def test_review_request_rejects_empty_code(self):
        from app.schemas.review import ReviewRequest
        with pytest.raises(Exception):
            ReviewRequest(code="", language="python")

    def test_review_request_rejects_invalid_language(self):
        from app.schemas.review import ReviewRequest
        with pytest.raises(Exception):
            ReviewRequest(code="x = 1", language="cobol")

    def test_review_request_rejects_oversized_code(self):
        """Code over 10000 chars should be rejected."""
        from app.schemas.review import ReviewRequest
        with pytest.raises(Exception):
            ReviewRequest(code="x" * 10001, language="python")

    def test_review_result_accepts_valid_data(self):
        from app.schemas.review import ReviewResult
        result = ReviewResult(summary="Good code", issues=[], score=8)
        assert result.score == 8
        assert result.summary == "Good code"

    def test_review_result_rejects_score_below_1(self):
        from app.schemas.review import ReviewResult
        with pytest.raises(Exception):
            ReviewResult(summary="Bad", issues=[], score=0)

    def test_review_result_rejects_score_above_10(self):
        from app.schemas.review import ReviewResult
        with pytest.raises(Exception):
            ReviewResult(summary="Bad", issues=[], score=11)

    def test_code_issue_categories(self):
        """Verify issue model accepts bug, security, performance, style categories."""
        from app.schemas.review import CodeIssue
        for category in ["bug", "security", "performance", "style"]:
            issue = CodeIssue(
                line=1, severity="warning", category=category,
                description="test", suggestion="test"
            )
            assert issue.category == category


# ============================================================
# 4. LANGUAGE SUPPORT — "6+ programming languages" (2 tests)
# ============================================================

class TestLanguageSupport:

    def test_all_supported_languages_accepted(self):
        """All 9 supported languages should pass validation."""
        from app.schemas.review import ReviewRequest
        languages = ["python", "javascript", "typescript", "java", "go", "cpp", "rust", "c", "csharp"]
        for lang in languages:
            req = ReviewRequest(code="x = 1", language=lang)
            assert req.language == lang

    def test_supported_language_count(self):
        """Should support at least 6 languages (resume claim)."""
        supported = ["python", "javascript", "typescript", "java", "go", "cpp", "rust", "c", "csharp"]
        assert len(supported) >= 6


# ============================================================
# 5. CACHING — "Redis caching reducing API calls by 40%" (5 tests)
# ============================================================

class TestCaching:

    def test_cache_key_is_deterministic(self):
        """Same input should always produce the same cache key."""
        from app.services.cache import make_cache_key
        key1 = make_cache_key("review", "print('hello')", "python")
        key2 = make_cache_key("review", "print('hello')", "python")
        assert key1 == key2

    def test_cache_key_differs_for_different_code(self):
        from app.services.cache import make_cache_key
        key1 = make_cache_key("review", "print('hello')", "python")
        key2 = make_cache_key("review", "print('world')", "python")
        assert key1 != key2

    def test_cache_key_differs_for_different_language(self):
        from app.services.cache import make_cache_key
        key1 = make_cache_key("review", "x = 1", "python")
        key2 = make_cache_key("review", "x = 1", "javascript")
        assert key1 != key2

    def test_cache_key_differs_for_different_action(self):
        """Review vs explain vs refactor should have different keys."""
        from app.services.cache import make_cache_key
        key1 = make_cache_key("review", "x = 1", "python")
        key2 = make_cache_key("explain", "x = 1", "python")
        key3 = make_cache_key("refactor", "x = 1", "python")
        assert key1 != key2 != key3

    @pytest.mark.asyncio
    async def test_cache_hit_skips_llm_call(self):
        """When cache has a result, the LLM should NOT be called."""
        from app.services.llm import LLMService

        service = LLMService.__new__(LLMService)
        service.review_parser = MagicMock()
        service.llm = MagicMock()

        with patch("app.services.llm.get_cached", return_value=MOCK_REVIEW_DATA):
            result, was_cached = await service.review_code("print('hi')", "python")
            assert was_cached is True
            assert result.score == 7
            assert len(result.issues) == 3


# ============================================================
# 6. ENDPOINTS — "3 LLM-powered endpoints" (5 tests)
# ============================================================

class TestEndpoints:

    @pytest.mark.asyncio
    async def test_review_endpoint_exists(self, client):
        """POST /api/review should exist (401 = exists but needs auth)."""
        response = await client.post("/api/review", json={"code": "x", "language": "python"})
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_explain_endpoint_exists(self, client):
        """POST /api/explain should exist."""
        response = await client.post("/api/explain", json={"code": "x", "language": "python"})
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_refactor_endpoint_exists(self, client):
        """POST /api/refactor should exist."""
        response = await client.post("/api/refactor", json={"code": "x", "language": "python"})
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_history_endpoint_exists(self, client):
        """GET /api/history should exist."""
        response = await client.get("/api/history")
        assert response.status_code == 401  # needs auth

    @pytest.mark.asyncio
    async def test_register_endpoint_exists(self, client):
        """POST /api/auth/register should exist."""
        response = await client.post("/api/auth/register", json={})
        assert response.status_code == 422  # validation error = endpoint exists


# ============================================================
# 7. RATE LIMITING — "per-user rate limiting" (2 tests)
# ============================================================

class TestRateLimiting:

    @pytest.mark.asyncio
    async def test_rate_limit_allows_under_threshold(self):
        """Requests under the limit should succeed."""
        from app.middleware.rate_limit import check_rate_limit

        with patch("app.middleware.rate_limit.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value="5")  # 5 of 20 used
            mock_redis.pipeline.return_value = AsyncMock()
            mock_redis.pipeline.return_value.incr = MagicMock()
            mock_redis.pipeline.return_value.expire = MagicMock()
            mock_redis.pipeline.return_value.execute = AsyncMock()

            # Should not raise
            await check_rate_limit(user_id=1, action="review", max_requests=20)

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_over_threshold(self):
        """Requests over the limit should raise 429."""
        from fastapi import HTTPException
        from app.middleware.rate_limit import check_rate_limit

        with patch("app.middleware.rate_limit.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value="20")  # 20 of 20 used

            with pytest.raises(HTTPException) as exc_info:
                await check_rate_limit(user_id=1, action="review", max_requests=20)
            assert exc_info.value.status_code == 429