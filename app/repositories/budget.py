from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.budget import Budget
from app.models.category import Category
from app.models.transaction import Transaction, TransactionType
from app.repositories.base import BaseRepository, _month_range


class BudgetRepository(BaseRepository[Budget]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Budget, session)

    async def get_all_by_owner(self, owner_id: int, month: date | None = None) -> list[Budget]:
        stmt = select(Budget).where(Budget.owner_id == owner_id)
        if month is not None:
            stmt = stmt.where(Budget.month == month)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id_and_owner(self, budget_id: int, owner_id: int) -> Budget | None:
        result = await self.session.execute(
            select(Budget).where(
                Budget.id == budget_id,
                Budget.owner_id == owner_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_category_and_month(
        self, owner_id: int, category_id: int, month: date
    ) -> Budget | None:
        result = await self.session.execute(
            select(Budget).where(
                Budget.owner_id == owner_id,
                Budget.category_id == category_id,
                Budget.month == month,
            )
        )
        return result.scalar_one_or_none()

    async def update(self, budget: Budget, **kwargs) -> Budget:
        for key, value in kwargs.items():
            setattr(budget, key, value)
        await self.session.flush()
        await self.session.refresh(budget)
        return budget

    async def get_usage(self, owner_id: int, month: date) -> list[dict]:
        """Return spending vs limit for every budget the user has this month."""
        start, end = _month_range(month)

        spending_sq = (
            select(
                Transaction.category_id,
                func.coalesce(func.sum(Transaction.amount), Decimal("0")).label("spent"),
            )
            .join(Account, Transaction.account_id == Account.id)
            .where(
                Account.owner_id == owner_id,
                Transaction.is_deleted == False,  # noqa: E712
                Transaction.type == TransactionType.EXPENSE,
                Transaction.date >= start,
                Transaction.date < end,
            )
            .group_by(Transaction.category_id)
            .subquery()
        )

        result = await self.session.execute(
            select(
                Budget.id,
                Budget.category_id,
                Category.name.label("category_name"),
                Budget.limit_amount,
                func.coalesce(spending_sq.c.spent, Decimal("0")).label("spent_amount"),
            )
            .join(Category, Budget.category_id == Category.id)
            .outerjoin(spending_sq, Budget.category_id == spending_sq.c.category_id)
            .where(Budget.owner_id == owner_id, Budget.month == month)
        )
        return [
            {
                "category_id": row.category_id,
                "category_name": row.category_name,
                "limit_amount": row.limit_amount,
                "spent_amount": row.spent_amount,
            }
            for row in result.all()
        ]
