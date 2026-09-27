from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"
    __table_args__ = (
        # Only transfers point at a destination, and never at their own source account.
        # (Transfers created before this column existed have no destination, so a transfer
        # without one is still allowed at the database level; the API requires it.)
        CheckConstraint(
            "to_account_id IS NULL OR type = 'TRANSFER'", name="ck_transactions_to_account_transfer"
        ),
        CheckConstraint(
            "to_account_id IS NULL OR to_account_id <> account_id",
            name="ck_transactions_to_account_differs",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    # Transfers only: the account that receives the money. account_id is the one it leaves.
    to_account_id: Mapped[int | None] = mapped_column(
        ForeignKey("accounts.id"), nullable=True, index=True
    )
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    type: Mapped[TransactionType] = mapped_column(SAEnum(TransactionType), nullable=False)
    # NUMERIC(12,2) — never use FLOAT for money
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Soft-delete — records are never physically removed
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    account: Mapped["Account"] = relationship(
        back_populates="transactions", foreign_keys=[account_id]
    )
    category: Mapped["Category"] = relationship(back_populates="transactions")
