from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recurring_transaction import RecurringTransaction
from app.repositories.base import BaseRepository


class RecurringTransactionRepository(BaseRepository[RecurringTransaction]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(RecurringTransaction, session)

    async def get_all_by_owner(self, owner_id: int) -> list[RecurringTransaction]:
        result = await self.session.execute(
            select(RecurringTransaction)
            .where(RecurringTransaction.owner_id == owner_id)
            .order_by(RecurringTransaction.next_due_date.asc())
        )
        return list(result.scalars().all())

    async def get_by_id_and_owner(
        self, recurring_id: int, owner_id: int
    ) -> RecurringTransaction | None:
        result = await self.session.execute(
            select(RecurringTransaction).where(
                RecurringTransaction.id == recurring_id,
                RecurringTransaction.owner_id == owner_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_due_on_or_before(self, cutoff: date) -> list[RecurringTransaction]:
        """Return all active templates whose next_due_date is on or before *cutoff*."""
        result = await self.session.execute(
            select(RecurringTransaction).where(
                RecurringTransaction.is_active == True,  # noqa: E712
                RecurringTransaction.next_due_date <= cutoff,
            )
        )
        return list(result.scalars().all())

    async def update(self, instance: RecurringTransaction, **kwargs) -> RecurringTransaction:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance
