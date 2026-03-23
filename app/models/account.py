from __future__ import annotations

from decimal import Decimal
from enum import Enum

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


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


class Account(Base, TimestampMixin):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[AccountType] = mapped_column(SAEnum(AccountType), nullable=False)
    currency: Mapped[CurrencyCode] = mapped_column(
        SAEnum(CurrencyCode), nullable=False, default=CurrencyCode.USD
    )
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    # Updated daily by Celery Beat — avoids summing all transactions on every request
    balance_snapshot: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )

    owner: Mapped["User"] = relationship(back_populates="accounts")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account")
