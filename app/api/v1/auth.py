from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_session
from app.models import Users
from app.schemas.auth import AdminCheckResponse, LoginRequest, TokenResponse
from app.services.auth import authenticate_user, create_user_token

router = APIRouter(prefix="/auth", tags=["Auth"])

ADMIN_CHECK_RESPONSES = {
    status.HTTP_401_UNAUTHORIZED: {
        "description": "Missing, expired, or invalid Bearer token.",
        "content": {
            "application/json": {
                "example": {"detail": "Could not validate credentials"},
            },
        },
    },
}


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    """Authenticate user by email and password.

    The endpoint accepts JSON credentials with ``username`` and ``password``.
    ``username`` is treated as the user's email. Both regular users and admins
    authenticate through this endpoint; admin access is determined later by the
    ``is_admin`` claim and database flag.
    """
    user = await authenticate_user(
        session=session,
        username=credentials.username,
        password=credentials.password,
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(access_token=create_user_token(user))


@router.get(
    "/is-admin",
    response_model=AdminCheckResponse,
    summary="Check admin privileges",
    responses=ADMIN_CHECK_RESPONSES,
)
async def check_is_admin(
    current_user: Annotated[Users, Depends(get_current_user)],
) -> AdminCheckResponse:
    """Check whether the current authenticated user is an administrator.

    The endpoint requires a valid Bearer token and returns the admin flag from
    the `users.is_admin` database field. It is intentionally available to any
    authenticated user, so clients can decide whether to show admin features.
    """
    return AdminCheckResponse(
        user_id=current_user.id,
        email=current_user.email,
        is_admin=current_user.is_admin,
    )
