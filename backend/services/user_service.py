from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.user import User
from backend.auth.jwt import hash_password, verify_password


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Look up a user by email address."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """Look up a user by username."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession, username: str, email: str, password: str, full_name: str | None = None
) -> User:
    """Create a new user with a hashed password."""
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
    )
    db.add(user)
    await db.flush()
    return user


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> User | None:
    """Authenticate by email+password. Returns the user or None."""
    user = await get_user_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        return None
    user.last_login = datetime.now(timezone.utc)
    await db.flush()
    return user


async def update_user_profile(
    db: AsyncSession, user: User, **fields
) -> User:
    """Update the given user's profile fields."""
    for key, value in fields.items():
        if value is not None:
            setattr(user, key, value)
    await db.flush()
    return user
