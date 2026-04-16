"""
Shared SQLAlchemy declarative base for all ORM models.

Every model class in ``app.models`` must inherit from ``Base`` so SQLAlchemy
can collect its table definition in one metadata registry. Alembic will later
use this metadata object to discover tables and generate migrations.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Root class for project ORM models.

    The class intentionally does not define columns of its own yet. It exists
    as the single metadata owner for mapped models such as ``Users`` and
    ``Accounts``.
    """
