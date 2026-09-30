from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import CurrencyCode
from app.repositories.transaction import TransactionRepository
from app.schemas.report import (
    CashFlowEntry,
    CashFlowResponse,
    CategoryBreakdown,
    CategoryBreakdownResponse,
    MonthlySummary,
)


class ReportService:
    def __init__(self, session: AsyncSession) -> None:
        self.tx_repo = TransactionRepository(session)

    async def _require_rates(
        self, user_id: int, base: CurrencyCode, date_from: date, date_to: date
    ) -> None:
        """422 instead of a wrong total when some amount can't be converted to `base`."""
        missing = await self.tx_repo.find_missing_rate(user_id, base, date_from, date_to)
        if missing is not None:
            currency, day = missing
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    f"No exchange rate from {currency.value} to {base.value} "
                    f"effective on or before {day.isoformat()}. "
                    "An admin can add one with POST /api/v1/exchange-rates."
                ),
            )

    async def monthly(self, user_id: int, month: date, base: CurrencyCode) -> MonthlySummary:
        await self._require_rates(user_id, base, month, _month_end(month))
        data = await self.tx_repo.get_monthly_summary(user_id, month, base)
        income = data["total_income"]
        expenses = data["total_expenses"]
        return MonthlySummary(
            month=month,
            currency=base,
            total_income=income,
            total_expenses=expenses,
            net=income - expenses,
        )

    async def category_breakdown(
        self, user_id: int, month: date, base: CurrencyCode
    ) -> CategoryBreakdownResponse:
        await self._require_rates(user_id, base, month, _month_end(month))
        rows = await self.tx_repo.get_category_breakdown(user_id, month, base)
        total = sum((r["total_amount"] for r in rows), Decimal("0"))
        breakdown = [
            CategoryBreakdown(
                category_id=r["category_id"],
                category_name=r["category_name"],
                total_amount=r["total_amount"],
                percentage=round(float(r["total_amount"] / total) * 100, 2) if total else 0.0,
            )
            for r in rows
        ]
        return CategoryBreakdownResponse(
            month=month,
            currency=base,
            total_expenses=total,
            breakdown=breakdown,
        )

    async def cashflow(
        self, user_id: int, date_from: date, date_to: date, base: CurrencyCode
    ) -> CashFlowResponse:
        await self._require_rates(user_id, base, date_from, date_to)
        rows = await self.tx_repo.get_cashflow(user_id, date_from, date_to, base)
        entries = [
            CashFlowEntry(
                period=r["period"],
                income=r["income"],
                expenses=r["expenses"],
                net=r["net"],
                cumulative_net=r["cumulative_net"],
            )
            for r in rows
        ]
        return CashFlowResponse(
            date_from=date_from, date_to=date_to, currency=base, entries=entries
        )


def _month_end(month: date) -> date:
    """Last day of the month that starts on `month`."""
    next_month = (month.replace(day=28) + timedelta(days=4)).replace(day=1)
    return next_month - timedelta(days=1)
