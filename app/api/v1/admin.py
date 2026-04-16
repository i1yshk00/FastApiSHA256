from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_admin
from app.core.security import get_password_hash_async
from app.db.session import get_session
from app.models import Users
from app.schemas import (
    AccountRead,
    AdminUserRead,
    AdminUserWithAccounts,
    UserCreate,
    UserUpdate,
)

router = APIRouter(prefix="/admin", tags=["Admin"])


def build_admin_user_read_response(user: Users) -> AdminUserRead:
    """Convert a Users ORM instance to admin user response schema."""
    return AdminUserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
    )


def build_admin_user_with_accounts_response(user: Users) -> AdminUserWithAccounts:
    """Convert a Users ORM instance with accounts to admin list response."""
    return AdminUserWithAccounts(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        accounts=[
            AccountRead(
                id=account.id,
                balance=account.balance,
            )
            for account in user.accounts
        ],
    )


async def get_user_or_404(session: AsyncSession, user_id: int) -> Users:
    """Return user by id or raise HTTP 404 for admin CRUD endpoints."""
    result = await session.execute(select(Users).where(Users.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


async def ensure_email_available(
    session: AsyncSession,
    email: str,
    current_user_id: int | None = None,
) -> None:
    """Raise HTTP 409 when email is already used by another user."""
    query = select(Users.id).where(Users.email == email)
    if current_user_id is not None:
        query = query.where(Users.id != current_user_id)

    result = await session.execute(query)
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )


@router.post(
    "/users",
    response_model=AdminUserRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    payload: UserCreate,
    current_admin: Annotated[Users, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AdminUserRead:
    """Create a new user account from admin-provided fields."""
    await ensure_email_available(session=session, email=payload.email)

    user = Users(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=await get_password_hash_async(payload.password),
        is_active=payload.is_active,
        is_admin=payload.is_admin,
    )
    session.add(user)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        ) from exc

    await session.refresh(user)
    return build_admin_user_read_response(user)


@router.get("/users", response_model=list[AdminUserWithAccounts])
async def get_users(
    current_admin: Annotated[Users, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[AdminUserWithAccounts]:
    """Return all users with accounts and balances for administrators."""
    result = await session.execute(
        select(Users).options(selectinload(Users.accounts)).order_by(Users.id),
    )
    users = result.scalars().all()

    return [build_admin_user_with_accounts_response(user) for user in users]


@router.patch("/users/{user_id}", response_model=AdminUserRead)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    current_admin: Annotated[Users, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AdminUserRead:
    """Update mutable user fields by id for administrators."""
    user = await get_user_or_404(session=session, user_id=user_id)
    update_data = payload.model_dump(exclude_unset=True)

    email = update_data.get("email")
    if email is not None:
        await ensure_email_available(
            session=session,
            email=email,
            current_user_id=user.id,
        )
        user.email = email

    if "full_name" in update_data:
        user.full_name = update_data["full_name"]
    if "password" in update_data:
        user.hashed_password = await get_password_hash_async(update_data["password"])
    if "is_active" in update_data:
        user.is_active = update_data["is_active"]
    if "is_admin" in update_data:
        user.is_admin = update_data["is_admin"]

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        ) from exc

    await session.refresh(user)
    return build_admin_user_read_response(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_admin: Annotated[Users, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    """Delete a user by id and return an empty 204 response."""
    user = await get_user_or_404(session=session, user_id=user_id)
    await session.delete(user)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
