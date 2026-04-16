from datetime import datetime

from pydantic import BaseModel, Field


class UserRead(BaseModel):
    id: int
    email: str
    full_name: str


class AccountRead(BaseModel):
    id: int
    balance: float


class TransactionRead(BaseModel):
    transaction_id: str
    account_id: int
    amount: float
    created_at: datetime


class UserCreate(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=255)
    is_active: bool = True
    is_admin: bool = False


class UserUpdate(BaseModel):
    email: str | None = Field(default=None, min_length=1, max_length=255)
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    password: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = None
    is_admin: bool | None = None


class AdminUserRead(UserRead):
    is_active: bool
    is_admin: bool


class AdminUserWithAccounts(AdminUserRead):
    accounts: list[AccountRead]
