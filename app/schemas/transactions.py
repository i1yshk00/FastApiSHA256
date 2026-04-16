from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class TransactionSignatureRequest(BaseModel):
    transaction_id: str = Field(min_length=36, max_length=36)
    account_id: int = Field(gt=0)
    user_id: int = Field(gt=0)
    amount: Decimal

    @field_validator("amount")
    @classmethod
    def validate_amount_is_not_zero(cls, value: Decimal) -> Decimal:
        """Reject zero transactions while allowing credits and debits."""
        if value == Decimal("0"):
            raise ValueError("Amount must not be zero")
        return value


class TransactionSignatureResponse(BaseModel):
    signature: str


class TransactionWebhookRequest(TransactionSignatureRequest):
    signature: str = Field(min_length=1)


class TransactionWebhookResponse(BaseModel):
    transaction_id: str
    account_id: int
    user_id: int
    amount: float
    balance: float
    status: str
