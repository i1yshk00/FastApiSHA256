import hashlib
import hmac
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Accounts, Transactions, Users
from app.schemas import TransactionWebhookRequest, TransactionWebhookResponse

TRANSACTION_STATUS_PROCESSED = "processed"
TRANSACTION_STATUS_ALREADY_PROCESSED = "already_processed"
TRANSACTION_PROCESSING_ATTEMPTS = 2


class TransactionWebhookError(Exception):
    """Base transaction webhook processing error."""


class InvalidTransactionSignatureError(TransactionWebhookError):
    """Raised when webhook signature does not match the payload."""


class TransactionUserNotFoundError(TransactionWebhookError):
    """Raised when webhook references a missing user."""


class TransactionAccountConflictError(TransactionWebhookError):
    """Raised when account id belongs to another user."""


class TransactionInsufficientFundsError(TransactionWebhookError):
    """Raised when debit transaction would make account balance non-positive."""


class TransactionIntegrityError(TransactionWebhookError):
    """Raised when database integrity protection rejects webhook processing."""


def format_transaction_amount(amount: Decimal) -> str:
    """Serialize Decimal amount exactly as required for signature hashing."""
    return format(amount, "f")


def build_transaction_signature(
    *,
    account_id: int,
    amount: Decimal,
    transaction_id: str,
    user_id: int,
    secret_key: str,
) -> str:
    """Build SHA256 signature for transaction webhook payload fields."""
    raw_signature = (
        f"{account_id}"
        f"{format_transaction_amount(amount)}"
        f"{transaction_id}"
        f"{user_id}"
        f"{secret_key}"
    )
    return hashlib.sha256(raw_signature.encode("utf-8")).hexdigest()


def verify_transaction_signature(payload: TransactionWebhookRequest) -> bool:
    """Compare provided webhook signature with the expected signature."""
    expected_signature = build_transaction_signature(
        account_id=payload.account_id,
        amount=payload.amount,
        transaction_id=payload.transaction_id,
        user_id=payload.user_id,
        secret_key=settings.EXTERNAL_SECRET_KEY,
    )
    return hmac.compare_digest(expected_signature, payload.signature)


async def build_existing_transaction_response(
    session: AsyncSession,
    transaction: Transactions,
) -> TransactionWebhookResponse:
    """Build idempotent webhook response for an already stored transaction."""
    account = await session.get(Accounts, transaction.account_id)
    balance = account.balance if account is not None else Decimal("0.00")

    return TransactionWebhookResponse(
        transaction_id=transaction.transaction_id,
        account_id=transaction.account_id,
        user_id=transaction.user_id,
        amount=transaction.amount,
        balance=balance,
        status=TRANSACTION_STATUS_ALREADY_PROCESSED,
    )


async def process_transaction_webhook(
    session: AsyncSession,
    payload: TransactionWebhookRequest,
) -> TransactionWebhookResponse:
    """Validate and persist a transaction webhook in an atomic operation."""
    if not verify_transaction_signature(payload):
        raise InvalidTransactionSignatureError()

    last_integrity_error: IntegrityError | None = None
    for _ in range(TRANSACTION_PROCESSING_ATTEMPTS):
        try:
            async with session.begin():
                return await process_transaction_webhook_in_transaction(
                    session=session,
                    payload=payload,
                )
        except IntegrityError as exc:
            await session.rollback()
            last_integrity_error = exc
            existing_transaction_result = await session.execute(
                select(Transactions).where(
                    Transactions.transaction_id == payload.transaction_id,
                ),
            )
            existing_transaction = existing_transaction_result.scalar_one_or_none()
            if existing_transaction is not None:
                return await build_existing_transaction_response(
                    session=session,
                    transaction=existing_transaction,
                )

    raise TransactionIntegrityError() from last_integrity_error


async def process_transaction_webhook_in_transaction(
    session: AsyncSession,
    payload: TransactionWebhookRequest,
) -> TransactionWebhookResponse:
    """Apply webhook business rules inside an opened database transaction."""
    existing_transaction_result = await session.execute(
        select(Transactions).where(
            Transactions.transaction_id == payload.transaction_id,
        ),
    )
    existing_transaction = existing_transaction_result.scalar_one_or_none()
    if existing_transaction is not None:
        return await build_existing_transaction_response(
            session=session,
            transaction=existing_transaction,
        )

    user = await session.get(Users, payload.user_id)
    if user is None:
        raise TransactionUserNotFoundError()

    account_result = await session.execute(
        select(Accounts).where(Accounts.id == payload.account_id).with_for_update(),
    )
    account = account_result.scalar_one_or_none()

    if account is None:
        if payload.amount < Decimal("0"):
            raise TransactionInsufficientFundsError()

        account = Accounts(
            id=payload.account_id,
            user_id=payload.user_id,
            balance=Decimal("0.00"),
        )
        session.add(account)
        await session.flush()
    elif account.user_id != payload.user_id:
        raise TransactionAccountConflictError()

    if payload.amount < Decimal("0"):
        new_balance = Decimal(str(account.balance)) + payload.amount
        if new_balance <= Decimal("0"):
            raise TransactionInsufficientFundsError()

    transaction_amount = payload.amount
    transaction = Transactions(
        transaction_id=payload.transaction_id,
        user_id=payload.user_id,
        account_id=payload.account_id,
        amount=transaction_amount,
    )
    session.add(transaction)

    account.balance += transaction_amount
    await session.flush()

    return TransactionWebhookResponse(
        transaction_id=transaction.transaction_id,
        account_id=transaction.account_id,
        user_id=transaction.user_id,
        amount=transaction.amount,
        balance=account.balance,
        status=TRANSACTION_STATUS_PROCESSED,
    )
