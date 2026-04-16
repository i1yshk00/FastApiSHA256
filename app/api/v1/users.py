from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_session
from app.models import Accounts, Transactions, Users
from app.schemas import AccountRead, TransactionRead, UserRead

router = APIRouter(prefix="/users", tags=["User"])


@router.get("/me", response_model=UserRead)
async def get_me(
    current_user: Annotated[Users, Depends(get_current_user)],
) -> UserRead:
    """Return current authenticated user's profile."""
    return UserRead(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
    )


@router.get("/me/accounts", response_model=list[AccountRead])
async def get_my_accounts(
    current_user: Annotated[Users, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[AccountRead]:
    """Return current authenticated user's accounts and balances."""
    result = await session.execute(
        select(Accounts)
        .where(Accounts.user_id == current_user.id)
        .order_by(Accounts.id),
    )
    accounts = result.scalars().all()

    return [
        AccountRead(
            id=account.id,
            balance=account.balance,
        )
        for account in accounts
    ]


@router.get("/me/transactions", response_model=list[TransactionRead])
async def get_my_transactions(
    current_user: Annotated[Users, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[TransactionRead]:
    """Return current authenticated user's account transactions."""
    result = await session.execute(
        select(Transactions)
        .where(Transactions.user_id == current_user.id)
        .order_by(Transactions.created_at.desc()),
    )
    transactions = result.scalars().all()

    return [
        TransactionRead(
            transaction_id=transaction.transaction_id,
            account_id=transaction.account_id,
            amount=transaction.amount,
            created_at=transaction.created_at,
        )
        for transaction in transactions
    ]
