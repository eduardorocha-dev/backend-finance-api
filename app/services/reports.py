from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

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

    async def monthly(self, user_id: int, month: date) -> MonthlySummary:
        data = await self.tx_repo.get_monthly_summary(user_id, month)
        income = data["total_income"]
        expenses = data["total_expenses"]
        return MonthlySummary(
            month=month,
            total_income=income,
            total_expenses=expenses,
            net=income - expenses,
        )

    async def category_breakdown(
        self, user_id: int, month: date
    ) -> CategoryBreakdownResponse:
        rows = await self.tx_repo.get_category_breakdown(user_id, month)
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
            total_expenses=total,
            breakdown=breakdown,
        )

    async def cashflow(
        self, user_id: int, date_from: date, date_to: date
    ) -> CashFlowResponse:
        rows = await self.tx_repo.get_cashflow(user_id, date_from, date_to)
        entries = [
            CashFlowEntry(
                period=r["period"],
                income=r["income"],
                expenses=r["expenses"],
                net=r["income"] - r["expenses"],
            )
            for r in rows
        ]
        return CashFlowResponse(date_from=date_from, date_to=date_to, entries=entries)
