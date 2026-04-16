"""
User balance account ORM model.

An account belongs to exactly one user and stores that user's balance. The
transaction webhook will use this model to find or create a target balance account
and then increase ``balance`` after a valid transaction.
"""

from typing import TYPE_CHECKING
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    # Imported only for static analysis to avoid runtime circular imports.
    from app.models import Transactions, Users


class Accounts(Base):
    """
    Balance account owned by a user.

    Fields:
        id: Integer primary key and internal account identifier.
        user_id: Required foreign key to ``users.id``. Indexed because account
            lists will usually be loaded by current user id.
        balance: Current account balance stored as ``Decimal``/``Numeric``.
        user: Parent ``Users`` ORM object.
        transactions: Processed top-up transactions for this account.

    Notes:
        PostgreSQL ``Numeric(18, 2)`` is used to avoid binary floating-point
        errors in balance calculations.
    """

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        server_default=text("0.00"),
        nullable=False,
    )

    # ORM-level access to the parent user; the database link itself is user_id.
    user: Mapped["Users"] = relationship("Users", back_populates="accounts")
    transactions: Mapped[list["Transactions"]] = relationship(
        "Transactions",
        back_populates="account",
        passive_deletes=True,
    )
