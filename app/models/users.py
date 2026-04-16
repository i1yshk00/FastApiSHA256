"""
User account ORM model.

The project treats administrators as regular users with elevated permissions.
That means there is no separate ``admins`` table: an admin is a row in
``users`` with ``is_admin=True``. Authorization code should check that flag
when protecting administrative endpoints.
"""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    # Imported only for static analysis to avoid runtime circular imports.
    from app.models import Accounts, Transactions


class Users(Base):
    """
    Application user and administrator identity.

    The table stores login credentials and authorization flags. A user can own
    multiple account records through the ``accounts`` relationship.

    Fields:
        id: Integer primary key used as the internal user identifier.
        email: Unique login email. Indexed for fast lookup during auth.
        full_name: User's display name returned by profile endpoints.
        hashed_password: Credential storage field containing a password hash,
            never a plain-text password.
        is_active: Allows disabling access without deleting the user row.
        is_admin: Grants access to administrative routes when set to ``True``.
        created_at: Server-side creation timestamp.
        updated_at: Server-side update timestamp.
        last_login_at: Nullable timestamp of the last successful login.
        accounts: Collection of the user's balance accounts.
        transactions: Collection of processed account transactions.

    Notes:
        The current design keeps administrators in the same table and uses the
        ``is_admin`` flag for authorization.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    last_login_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Deleting a user deletes owned accounts at ORM level.
    accounts: Mapped[list["Accounts"]] = relationship(
        "Accounts",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    transactions: Mapped[list["Transactions"]] = relationship(
        "Transactions",
        back_populates="user",
        passive_deletes=True,
    )
