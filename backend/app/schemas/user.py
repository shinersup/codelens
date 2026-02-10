"""
User schemas — Pydantic models for request/response validation.
"""

from pydantic import BaseModel


class UserCreate(BaseModel):
    """What the user sends to register."""
    email: str
    username: str
    password: str  # plain text — we hash it before storing


class UserLogin(BaseModel):
    """What the user sends to log in."""
    email: str
    password: str


class UserResponse(BaseModel):
    """What we send back (NEVER includes password)."""
    id: int
    email: str
    username: str

    class Config:
        from_attributes = True  # allows creating from SQLAlchemy model


class Token(BaseModel):
    """JWT token response after login."""
    access_token: str
    token_type: str = "bearer"
