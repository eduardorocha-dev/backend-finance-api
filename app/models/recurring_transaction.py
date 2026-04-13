from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.transaction import TransactionType


class RecurringFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class RecurringTransaction(Base, TimestampMixin):
    __tablename__ = "recurring_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    type: Mapped[TransactionType] = mapped_column(
        SAEnum(TransactionType, create_type=False), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    frequency: Mapped[RecurringFrequency] = mapped_column(
        SAEnum(RecurringFrequency, name="recurringfrequency"), nullable=False
    )
    next_due_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    account: Mapped["Account"] = relationship()  # noqa: F821
    category: Mapped["Category"] = relationship()  # noqa: F821
