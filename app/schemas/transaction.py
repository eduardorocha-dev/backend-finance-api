from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, field_validator, model_validator


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


# ── Incoming ──────────────────────────────────────────────────────────────────


class TransactionCreate(BaseModel):
    account_id: int
    # transfers only: the account receiving the money (account_id is the one it leaves)
    to_account_id: int | None = None
    category_id: int
    type: TransactionType
    amount: Decimal
    description: str | None = None
    date: datetime

    # amount must always be a positive number —
    # the type field (income/expense) is what determines direction
    @field_validator("amount")
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return v

    @model_validator(mode="after")
    def destination_only_for_transfers(self):
        if self.type == TransactionType.TRANSFER:
            if self.to_account_id is None:
                raise ValueError("A transfer needs a to_account_id")
            if self.to_account_id == self.account_id:
                raise ValueError("Cannot transfer to the same account")
        elif self.to_account_id is not None:
            raise ValueError("Only transfers can have a to_account_id")
        return self


class TransactionUpdate(BaseModel):
    category_id: int | None = None
    description: str | None = None
    date: datetime | None = None

    # NOTE: amount and type are intentionally NOT updatable.
    # Transactions are immutable records — to fix a mistake
    # the user deletes and recreates, or creates a correction entry.


class TransactionFilter(BaseModel):
    account_id: int | None = None
    category_id: int | None = None
    type: TransactionType | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


# ── Outgoing ──────────────────────────────────────────────────────────────────


class TransactionRead(BaseModel):
    id: int
    account_id: int
    to_account_id: int | None
    category_id: int
    type: TransactionType
    amount: Decimal
    description: str | None
    date: datetime
    is_deleted: bool
    created_at: datetime

    model_config = {"from_attributes": True}
