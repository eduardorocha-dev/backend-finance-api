from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import CurrencyCode
from app.models.exchange_rate import ExchangeRate
from app.repositories.exchange_rate import ExchangeRateRepository
from app.schemas.exchange_rate import (
    ConvertRequest,
    ConvertResponse,
    ExchangeRateCreate,
    ExchangeRateRead,
    ExchangeRateUpdate,
)

_SIX = Decimal("0.000001")
_TWO = Decimal("0.01")


class ExchangeRateService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = ExchangeRateRepository(session)

    async def create(self, data: ExchangeRateCreate) -> ExchangeRate:
        existing = await self.repo.get_on_date(
            data.from_currency,  # type: ignore[arg-type]
            data.to_currency,  # type: ignore[arg-type]
            data.effective_date,
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A rate for this pair and date already exists",
            )
        return await self.repo.create(
            from_currency=data.from_currency,
            to_currency=data.to_currency,
            rate=data.rate.quantize(_SIX, rounding=ROUND_HALF_UP),
            effective_date=data.effective_date,
        )

    async def get(self, exchange_rate_id: int) -> ExchangeRate:
        er = await self.repo.get_by_id(exchange_rate_id)
        if er is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Exchange rate not found"
            )
        return er

    async def update(self, exchange_rate_id: int, data: ExchangeRateUpdate) -> ExchangeRate:
        er = await self.get(exchange_rate_id)
        return await self.repo.update(
            er, rate=data.rate.quantize(_SIX, rounding=ROUND_HALF_UP)
        )

    async def delete(self, exchange_rate_id: int) -> None:
        er = await self.get(exchange_rate_id)
        await self.repo.delete(er)

    async def list_for_pair(
        self,
        from_currency: CurrencyCode,
        to_currency: CurrencyCode,
        limit: int = 30,
    ) -> list[ExchangeRate]:
        return await self.repo.list_for_pair(from_currency, to_currency, limit)

    async def get_latest(
        self, from_currency: CurrencyCode, to_currency: CurrencyCode
    ) -> ExchangeRateRead:
        er = await self.repo.get_latest(from_currency, to_currency)
        if er is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No exchange rate found for {from_currency}/{to_currency}",
            )
        return ExchangeRateRead.model_validate(er)

    async def convert(self, data: ConvertRequest) -> ConvertResponse:
        if data.from_currency == data.to_currency:
            return ConvertResponse(
                from_currency=data.from_currency,
                to_currency=data.to_currency,
                original_amount=data.amount,
                converted_amount=data.amount,
                rate=Decimal("1.000000"),
                effective_date=__import__("datetime").date.today(),
            )

        er = await self.repo.get_latest(
            data.from_currency,  # type: ignore[arg-type]
            data.to_currency,  # type: ignore[arg-type]
        )
        if er is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No exchange rate found for {data.from_currency}/{data.to_currency}",
            )

        converted = (data.amount * er.rate).quantize(_TWO, rounding=ROUND_HALF_UP)
        return ConvertResponse(
            from_currency=data.from_currency,
            to_currency=data.to_currency,
            original_amount=data.amount,
            converted_amount=converted,
            rate=er.rate,
            effective_date=er.effective_date,
        )
