from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.repositories.base import BaseRepository


class AccountRepository(BaseRepository[Account]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Account, session)

    async def get_all_by_owner(self, owner_id: int) -> list[Account]:
        result = await self.session.execute(
            select(Account).where(Account.owner_id == owner_id)
        )
        return list(result.scalars().all())

    async def get_by_id_and_owner(
        self, account_id: int, owner_id: int
    ) -> Account | None:
        result = await self.session.execute(
            select(Account).where(
                Account.id == account_id,
                Account.owner_id == owner_id,
            )
        )
        return result.scalar_one_or_none()

    async def update(self, account: Account, **kwargs) -> Account:
        for key, value in kwargs.items():
            setattr(account, key, value)
        await self.session.flush()
        await self.session.refresh(account)
        return account

    async def update_balance_snapshot(
        self, account: Account, balance: Decimal
    ) -> Account:
        account.balance_snapshot = balance
        await self.session.flush()
        await self.session.refresh(account)
        return account
