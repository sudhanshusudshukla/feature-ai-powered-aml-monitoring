"""Security domain schemas for request/response DTOs."""
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request with email and password."""
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginResponse(BaseModel):
    """Login response with JWT token and user info."""
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    """User information returned after authentication."""
    id: int
    username: str
    full_name: str
    role: str

    class Config:
        from_attributes = True
