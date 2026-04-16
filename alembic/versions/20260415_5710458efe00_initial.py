"""initial

Revision ID: 5710458efe00
Revises:
Create Date: 2026-04-15 19:35:26.178192+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5710458efe00"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

USER_PASSWORD_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$4inIu0K7xoE37fnx3g0bzA"
    "$tvYVJ/ZIwIHsEXw6HQRhZHk2stoYXdaL7HQsENstIks"
)
ADMIN_PASSWORD_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$K2RvodmVYH4oqlezspHiFg"
    "$2dUFgOmGgPHvVNJX4iiSdGqsBS0mcrd2CxWPYsC2WjE"
)


def upgrade() -> None:
    """Create initial users, accounts, transactions tables, and seed data."""
    users_table = op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    accounts_table = op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("balance", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_accounts_user_id"), "accounts", ["user_id"])

    op.create_table(
        "transactions",
        sa.Column("transaction_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("transaction_id"),
    )
    op.create_index(op.f("ix_transactions_account_id"), "transactions", ["account_id"])
    op.create_index(op.f("ix_transactions_user_id"), "transactions", ["user_id"])

    op.bulk_insert(
        users_table,
        [
            {
                "id": 1,
                "email": "user@example.com",
                "full_name": "Test User",
                "hashed_password": USER_PASSWORD_HASH,
                "is_active": True,
                "is_admin": False,
            },
            {
                "id": 2,
                "email": "admin@example.com",
                "full_name": "Test Admin",
                "hashed_password": ADMIN_PASSWORD_HASH,
                "is_active": True,
                "is_admin": True,
            },
        ],
    )
    op.bulk_insert(
        accounts_table,
        [
            {
                "id": 1,
                "user_id": 1,
                "balance": 0.0,
            },
        ],
    )

    op.execute("SELECT setval('users_id_seq', (SELECT max(id) FROM users))")
    op.execute("SELECT setval('accounts_id_seq', (SELECT max(id) FROM accounts))")


def downgrade() -> None:
    """Drop initial schema objects in reverse dependency order."""
    op.drop_index(op.f("ix_transactions_user_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_account_id"), table_name="transactions")
    op.drop_table("transactions")
    op.drop_index(op.f("ix_accounts_user_id"), table_name="accounts")
    op.drop_table("accounts")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
