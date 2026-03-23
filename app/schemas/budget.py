from datetime import date
from decimal import Decimal

from pydantic import BaseModel, field_validator

# ── Incoming ──────────────────────────────────────────────────────────────────


class BudgetCreate(BaseModel):
    category_id: int
    limit_amount: Decimal
    # month is always the first day of the month, e.g. 2024-03-01
    # this makes it easy to query "all budgets for March 2024"
    month: date

    @field_validator("limit_amount")
    def limit_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Budget limit must be greater than zero")
        return v

    @field_validator("month")
    def month_must_be_first_day(cls, v):
        if v.day != 1:
            raise ValueError(
                "Month must be the first day of the month, e.g. 2024-03-01"
            )
        return v


class BudgetUpdate(BaseModel):
    limit_amount: Decimal | None = None


# ── Outgoing ──────────────────────────────────────────────────────────────────


class BudgetRead(BaseModel):
    id: int
    category_id: int
    limit_amount: Decimal
    month: date
    owner_id: int

    model_config = {"from_attributes": True}


class BudgetUsage(BaseModel):
    category_id: int
    category_name: str
    limit_amount: Decimal
    spent_amount: Decimal
    remaining_amount: Decimal
    usage_percentage: float
    # True when spending has passed the 80% alert threshold
    alert_triggered: bool
