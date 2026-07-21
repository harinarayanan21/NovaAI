from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class UserResponse(BaseModel):
    """Schema for user data in API responses."""

    id: str
    username: str
    email: str
    full_name: str | None
    profile_picture: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Schema for user profile updates."""

    full_name: str | None = Field(None, max_length=100)
    username: str | None = Field(None, min_length=3, max_length=50)
    profile_picture: str | None = Field(None, max_length=500)
