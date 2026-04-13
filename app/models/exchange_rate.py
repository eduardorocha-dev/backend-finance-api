from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, Numeric, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.account import CurrencyCode


class ExchangeRate(Base, TimestampMixin):
    __tablename__ = "exchange_rates"

    id: Mapped[int] = mapped_column(primary_key=True)
    from_currency: Mapped[CurrencyCode] = mapped_column(
        SAEnum(CurrencyCode, create_type=False), nullable=False
    )
    to_currency: Mapped[CurrencyCode] = mapped_column(
        SAEnum(CurrencyCode, create_type=False), nullable=False
    )
    # 6 decimal places — exchange rates need more precision than money amounts
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "from_currency", "to_currency", "effective_date",
            name="uq_exchange_rate_pair_date",
        ),
        CheckConstraint(
            "from_currency != to_currency", name="ck_exchange_rate_different_currencies"
        ),
        CheckConstraint("rate > 0", name="ck_exchange_rate_positive"),
    )
