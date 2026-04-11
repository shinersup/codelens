"""
Review schemas — these define the structure of code review requests and responses.

CodeIssue and ReviewResult models are especially important because
they are used to force the LLM to return structured JSON instead of freeform text.
"""

from typing import Any

from pydantic import BaseModel, Field


# --- Request ---

class ReviewRequest(BaseModel):
    """What the user sends to get a code review."""
    code: str = Field(..., min_length=1, max_length=10000)
    language: str = Field(..., pattern="^(python|javascript|typescript|java|go|cpp|rust|c|csharp)$")


# --- LLM structured output ---

class CodeIssue(BaseModel):
    """A single issue found in the code."""
    line: int | None = Field(default=None, description="Line number if applicable")
    severity: str = Field(description="critical, warning, or info")
    category: str = Field(description="bug, security, performance, or style")
    description: str = Field(description="What the issue is")
    suggestion: str = Field(description="How to fix it")
    verified: bool = Field(default=True, description="Whether the line number was verified against actual code")
    original_line: int | None = Field(default=None, description="Original line if corrected")


class ReviewResult(BaseModel):
    """Full structured review from the LLM."""
    summary: str = Field(description="2-3 sentence overall assessment")
    issues: list[CodeIssue] = Field(default_factory=list)
    score: int = Field(ge=1, le=10, description="Code quality score 1-10")


# --- API Responses ---

class ReviewResponse(BaseModel):
    """What we send back for a code review."""
    review: ReviewResult
    cached: bool = False


class ExplainResponse(BaseModel):
    """What we send back for code explanation."""
    explanation: str
    cached: bool = False


class RefactorResponse(BaseModel):
    """What we send back for refactor suggestions."""
    suggestions: str
    cached: bool = False


class HistoryItem(BaseModel):
    """Single item in review history list."""
    id: int
    language: str
    review_type: str
    score: int | None
    created_at: str

    class Config:
        from_attributes = True


class HistoryPage(BaseModel):
    """Paginated history response."""
    items: list[HistoryItem]
    next_cursor: int | None  # ID to pass as after_id for the next page; None = no more results


class HistoryDetail(BaseModel):
    """Full detail of a single past review."""
    id: int
    code: str
    language: str
    review_type: str
    result: Any
    score: int | None
    created_at: str

    class Config:
        from_attributes = True