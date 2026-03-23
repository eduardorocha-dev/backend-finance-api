from decimal import Decimal
from enum import Enum

from pydantic import BaseModel


class AccountType(str, Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT = "credit"
    CASH = "cash"


class CurrencyCode(str, Enum):
    USD = "USD"
    EUR = "EUR"
    BRL = "BRL"
    GBP = "GBP"


# ── Incoming ──────────────────────────────────────────────────────────────────


class AccountCreate(BaseModel):
    name: str
    type: AccountType
    currency: CurrencyCode = CurrencyCode.USD


class AccountUpdate(BaseModel):
    name: str | None = None
    currency: CurrencyCode | None = None


# ── Outgoing ──────────────────────────────────────────────────────────────────


class AccountRead(BaseModel):
    id: int
    name: str
    type: AccountType
    currency: CurrencyCode
    owner_id: int

    model_config = {"from_attributes": True}


class BalanceResponse(BaseModel):
    account_id: int
    account_name: str
    currency: CurrencyCode
    balance: Decimal
