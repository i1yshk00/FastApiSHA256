from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from anyio import to_thread
from jwt import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plain password against an Argon2 password hash."""
    return password_hash.verify(plain_password, hashed_password)


async def verify_password_async(plain_password: str, hashed_password: str) -> bool:
    """Check a password hash in a worker thread to keep event loop responsive."""
    return await to_thread.run_sync(verify_password, plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Create an Argon2 password hash for storing user credentials."""
    return password_hash.hash(password)


async def get_password_hash_async(password: str) -> str:
    """Create a password hash in a worker thread to avoid blocking async routes."""
    return await to_thread.run_sync(get_password_hash, password)


def create_access_token(
    subject: str | int,
    additional_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token for the given subject."""
    now = datetime.now(UTC)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
    }
    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except InvalidTokenError as exc:
        raise ValueError("Invalid access token") from exc
