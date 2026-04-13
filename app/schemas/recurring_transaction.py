from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, field_validator

from app.schemas.account import CurrencyCode  # noqa: F401 (re-exported for convenience)
from app.schemas.transaction import TransactionType


class RecurringFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class RecurringTransactionCreate(BaseModel):
    account_id: int
    category_id: int
    type: TransactionType
    amount: Decimal
    description: str | None = None
    frequency: RecurringFrequency
    next_due_date: date

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("amount must be positive")
        return v


class RecurringTransactionUpdate(BaseModel):
    amount: Decimal | None = None
    description: str | None = None
    frequency: RecurringFrequency | None = None
    next_due_date: date | None = None
    is_active: bool | None = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("amount must be positive")
        return v


class RecurringTransactionRead(BaseModel):
    id: int
    owner_id: int
    account_id: int
    category_id: int
    type: TransactionType
    amount: Decimal
    description: str | None
    frequency: RecurringFrequency
    next_due_date: date
    is_active: bool

    model_config = {"from_attributes": True}
