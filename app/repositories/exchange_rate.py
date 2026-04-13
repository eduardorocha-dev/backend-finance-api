from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import CurrencyCode
from app.models.exchange_rate import ExchangeRate
from app.repositories.base import BaseRepository


class ExchangeRateRepository(BaseRepository[ExchangeRate]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ExchangeRate, session)

    async def get_latest(
        self, from_currency: CurrencyCode, to_currency: CurrencyCode
    ) -> ExchangeRate | None:
        """Return the most recent rate for a currency pair."""
        result = await self.session.execute(
            select(ExchangeRate)
            .where(
                ExchangeRate.from_currency == from_currency,
                ExchangeRate.to_currency == to_currency,
            )
            .order_by(ExchangeRate.effective_date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_on_date(
        self,
        from_currency: CurrencyCode,
        to_currency: CurrencyCode,
        effective_date: date,
    ) -> ExchangeRate | None:
        """Return the rate for a pair on a specific date."""
        result = await self.session.execute(
            select(ExchangeRate).where(
                ExchangeRate.from_currency == from_currency,
                ExchangeRate.to_currency == to_currency,
                ExchangeRate.effective_date == effective_date,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_pair(
        self,
        from_currency: CurrencyCode,
        to_currency: CurrencyCode,
        limit: int = 30,
    ) -> list[ExchangeRate]:
        """Return recent rates for a pair, newest first."""
        result = await self.session.execute(
            select(ExchangeRate)
            .where(
                ExchangeRate.from_currency == from_currency,
                ExchangeRate.to_currency == to_currency,
            )
            .order_by(ExchangeRate.effective_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update(self, exchange_rate: ExchangeRate, **kwargs) -> ExchangeRate:
        for key, value in kwargs.items():
            setattr(exchange_rate, key, value)
        await self.session.flush()
        await self.session.refresh(exchange_rate)
        return exchange_rate
