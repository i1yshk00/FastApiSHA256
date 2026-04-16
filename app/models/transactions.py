"""
Account transaction ORM model.

The model stores processed transaction webhooks. The external ``transaction_id``
is unique, so the same transaction cannot be applied to an account balance twice.

The webhook payload also contains ``signature``. The application should verify
that value before creating a transaction, but the signature itself is not part
of the transaction history and is intentionally not persisted here.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    # Imported only for static analysis to avoid runtime circular imports.
    from app.models import Accounts, Users


class Transactions(Base):
    """Processed balance top-up transaction.

    Fields:
        transaction_id: UUID transaction id from the external system.
            This field is the primary key and provides webhook idempotency.
        user_id: User that owns the target account.
        account_id: Account that receives the balance top-up.
        amount: Transaction amount from the webhook payload.
        created_at: Server-side timestamp when the transaction was stored.
        user: Parent ``Users`` ORM object.
        account: Parent ``Accounts`` ORM object.
    """

    __tablename__ = "transactions"

    transaction_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # ORM-level accessors; the database links themselves are user_id/account_id.
    user: Mapped["Users"] = relationship("Users", back_populates="transactions")
    account: Mapped["Accounts"] = relationship(
        "Accounts",
        back_populates="transactions",
    )
