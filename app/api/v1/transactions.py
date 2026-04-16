from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_session
from app.schemas import (
    TransactionSignatureRequest,
    TransactionSignatureResponse,
    TransactionWebhookRequest,
    TransactionWebhookResponse,
)
from app.services.transactions import (
    InvalidTransactionSignatureError,
    TransactionAccountConflictError,
    TransactionInsufficientFundsError,
    TransactionIntegrityError,
    TransactionUserNotFoundError,
    build_transaction_signature,
    process_transaction_webhook,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/signature", response_model=TransactionSignatureResponse)
async def create_transaction_signature(
    payload: TransactionSignatureRequest,
) -> TransactionSignatureResponse:
    """Build transaction webhook signature for manual testing."""
    signature = build_transaction_signature(
        account_id=payload.account_id,
        amount=payload.amount,
        transaction_id=payload.transaction_id,
        user_id=payload.user_id,
        secret_key=settings.EXTERNAL_SECRET_KEY,
    )
    return TransactionSignatureResponse(signature=signature)


@router.post("/webhook", response_model=TransactionWebhookResponse)
async def process_webhook(
    payload: TransactionWebhookRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TransactionWebhookResponse:
    """Process external transaction webhook and update account balance."""
    try:
        return await process_transaction_webhook(session=session, payload=payload)
    except InvalidTransactionSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid transaction signature",
        ) from exc
    except TransactionUserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        ) from exc
    except TransactionAccountConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account belongs to another user",
        ) from exc
    except TransactionInsufficientFundsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account balance must remain positive",
        ) from exc
    except TransactionIntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transaction webhook could not be processed",
        ) from exc
