from __future__ import annotations

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget
from app.repositories.budget import BudgetRepository
from app.repositories.category import CategoryRepository
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetUsage

_ALERT_THRESHOLD = 0.80


class BudgetService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = BudgetRepository(session)
        self.cat_repo = CategoryRepository(session)

    async def list(self, user_id: int, month: date | None = None) -> list[Budget]:
        return await self.repo.get_all_by_owner(user_id, month)

    async def create(self, user_id: int, data: BudgetCreate) -> Budget:
        category = await self.cat_repo.get_by_id_and_owner(data.category_id, user_id)
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        existing = await self.repo.get_by_category_and_month(user_id, data.category_id, data.month)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A budget for this category and month already exists",
            )

        return await self.repo.create(
            owner_id=user_id,
            category_id=data.category_id,
            limit_amount=data.limit_amount,
            month=data.month,
        )

    async def get(self, user_id: int, budget_id: int) -> Budget:
        budget = await self.repo.get_by_id_and_owner(budget_id, user_id)
        if budget is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
        return budget

    async def update(self, user_id: int, budget_id: int, data: BudgetUpdate) -> Budget:
        budget = await self.get(user_id, budget_id)
        updates = data.model_dump(exclude_none=True)
        if not updates:
            return budget
        return await self.repo.update(budget, **updates)

    async def delete(self, user_id: int, budget_id: int) -> None:
        budget = await self.get(user_id, budget_id)
        await self.repo.delete(budget)

    async def get_usage(self, user_id: int, month: date) -> list[BudgetUsage]:
        rows = await self.repo.get_usage(user_id, month)
        result = []
        for row in rows:
            limit = row["limit_amount"]
            spent = row["spent_amount"]
            remaining = limit - spent
            pct = float(spent / limit) if limit else 0.0
            result.append(
                BudgetUsage(
                    category_id=row["category_id"],
                    category_name=row["category_name"],
                    limit_amount=limit,
                    spent_amount=spent,
                    remaining_amount=remaining,
                    usage_percentage=round(pct * 100, 2),
                    alert_triggered=pct >= _ALERT_THRESHOLD,
                )
            )
        return result
