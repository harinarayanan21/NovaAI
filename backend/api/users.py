from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.session import get_db
from backend.auth.jwt import get_current_user
from backend.models.user import User
from backend.schemas.user import UserResponse, UserUpdate
from backend.services.user_service import update_user_profile, get_user_by_username

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    request: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the authenticated user's profile."""
    if request.username and request.username != current_user.username:
        existing = await get_user_by_username(db, request.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken.",
            )

    updated = await update_user_profile(
        db,
        current_user,
        full_name=request.full_name,
        username=request.username,
        profile_picture=request.profile_picture,
    )
    return updated
