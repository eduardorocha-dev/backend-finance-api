from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recurring_transaction import RecurringTransaction
from app.repositories.recurring_transaction import RecurringTransactionRepository
from app.schemas.recurring_transaction import (
    RecurringTransactionCreate,
    RecurringTransactionUpdate,
)


class RecurringTransactionService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = RecurringTransactionRepository(session)

    async def list(self, owner_id: int) -> list[RecurringTransaction]:
        return await self.repo.get_all_by_owner(owner_id)

    async def create(self, owner_id: int, data: RecurringTransactionCreate) -> RecurringTransaction:
        return await self.repo.create(
            owner_id=owner_id,
            account_id=data.account_id,
            category_id=data.category_id,
            type=data.type,
            amount=data.amount,
            description=data.description,
            frequency=data.frequency,
            next_due_date=data.next_due_date,
        )

    async def get(self, owner_id: int, recurring_id: int) -> RecurringTransaction:
        rt = await self.repo.get_by_id_and_owner(recurring_id, owner_id)
        if rt is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recurring transaction not found",
            )
        return rt

    async def update(
        self, owner_id: int, recurring_id: int, data: RecurringTransactionUpdate
    ) -> RecurringTransaction:
        rt = await self.get(owner_id, recurring_id)
        updates = data.model_dump(exclude_none=True)
        if not updates:
            return rt
        return await self.repo.update(rt, **updates)

    async def delete(self, owner_id: int, recurring_id: int) -> None:
        rt = await self.get(owner_id, recurring_id)
        await self.repo.delete(rt)
