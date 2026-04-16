# ruff: noqa: E402, I001

import os
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-with-at-least-32-bytes")
os.environ.setdefault("EXTERNAL_SECRET_KEY", "gfdmhghif38yrf9ew0jkf32")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.security import get_password_hash  # noqa: E402
from app.db.session import get_session  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Accounts, Base, Users  # noqa: E402

TEST_USER_EMAIL = "user@example.com"
TEST_USER_PASSWORD = "user12345"
TEST_ADMIN_EMAIL = "admin@example.com"
TEST_ADMIN_PASSWORD = "admin12345"


@pytest_asyncio.fixture
async def test_engine() -> AsyncGenerator[AsyncEngine]:
    """Create isolated in-memory SQLite engine for one test."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def test_session_factory(
    test_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Create session factory and seed default test users/accounts."""
    session_factory = async_sessionmaker(
        bind=test_engine,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        session.add_all(
            [
                Users(
                    id=1,
                    email=TEST_USER_EMAIL,
                    full_name="Test User",
                    hashed_password=get_password_hash(TEST_USER_PASSWORD),
                    is_active=True,
                    is_admin=False,
                ),
                Users(
                    id=2,
                    email=TEST_ADMIN_EMAIL,
                    full_name="Test Admin",
                    hashed_password=get_password_hash(TEST_ADMIN_PASSWORD),
                    is_active=True,
                    is_admin=True,
                ),
                Accounts(
                    id=1,
                    user_id=1,
                    balance=0.0,
                ),
            ],
        )
        await session.commit()

    return session_factory


@pytest_asyncio.fixture
async def client(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncClient]:
    """Return HTTP client with database session dependency overridden."""

    async def override_get_session() -> AsyncGenerator[AsyncSession]:
        """Yield test database session through FastAPI dependency override."""
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as async_client:
            yield async_client
    finally:
        app.dependency_overrides.clear()
