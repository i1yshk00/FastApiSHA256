from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, verify_password_async
from app.models import Users


async def authenticate_user(
    session: AsyncSession,
    username: str,
    password: str,
) -> Users | None:
    """Authenticate an active user by email and password."""
    result = await session.execute(select(Users).where(Users.email == username))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        return None

    if not await verify_password_async(password, user.hashed_password):
        return None

    user.last_login_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(user)
    return user


def create_user_token(user: Users) -> str:
    """Create a JWT access token containing user identity and admin flag."""
    return create_access_token(
        subject=user.id,
        additional_claims={
            "email": user.email,
            "is_admin": user.is_admin,
        },
    )
