from fastapi import APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from backend.database.session import get_db
from backend.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
)
from backend.services.user_service import (
    create_user,
    get_user_by_email,
    get_user_by_username,
    authenticate_user,
)
from backend.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    validate_password_strength,
)
from backend.utils.logger import logger

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user and return JWT tokens."""
    error = validate_password_strength(request.password)
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    if await get_user_by_email(db, request.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered."
        )
    if await get_user_by_username(db, request.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already taken."
        )

    user = await create_user(
        db, request.username, request.email, request.password, request.full_name
    )
    logger.info("New user registered: %s (%s)", user.username, user.email)

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate a user and return JWT tokens."""
    user = await authenticate_user(db, request.email, request.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    logger.info("User logged in: %s", user.username)

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a valid refresh token for new access + refresh tokens."""
    payload = decode_token(request.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type.",
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
        )

    from sqlalchemy import select
    from backend.models.user import User

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
        )

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout():
    """Logout endpoint. Client should discard tokens."""
    return None
