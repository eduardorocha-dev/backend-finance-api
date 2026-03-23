from datetime import date
from decimal import Decimal

from pydantic import BaseModel

# Reports have no incoming Create/Update schemas —
# they are read-only views driven by query parameters.
# The query parameters will be defined directly in the endpoint functions.


# ── Outgoing ──────────────────────────────────────────────────────────────────


class MonthlySummary(BaseModel):
    month: date
    total_income: Decimal
    total_expenses: Decimal
    net: Decimal  # total_income - total_expenses


class CategoryBreakdown(BaseModel):
    category_id: int
    category_name: str
    total_amount: Decimal
    # percentage of total spending this category represents
    percentage: float


class CategoryBreakdownResponse(BaseModel):
    month: date
    total_expenses: Decimal
    breakdown: list[CategoryBreakdown]


class CashFlowEntry(BaseModel):
    # a single day or week entry in the cash flow report
    period: date
    income: Decimal
    expenses: Decimal
    net: Decimal


class CashFlowResponse(BaseModel):
    date_from: date
    date_to: date
    entries: list[CashFlowEntry]
