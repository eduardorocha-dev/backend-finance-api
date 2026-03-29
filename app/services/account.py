from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.account import Account
from app.repositories.account import AccountRepository
from app.repositories.transaction import TransactionRepository
from app.schemas.account import AccountCreate, AccountUpdate, BalanceResponse


class AccountService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = AccountRepository(session)
        self.tx_repo = TransactionRepository(session)

    async def list(self, user_id: int) -> list[Account]:
        return await self.repo.get_all_by_owner(user_id)

    async def create(self, user_id: int, data: AccountCreate) -> Account:
        return await self.repo.create(
            owner_id=user_id,
            name=data.name,
            type=data.type,
            currency=data.currency,
        )

    async def get(self, user_id: int, account_id: int) -> Account:
        account = await self.repo.get_by_id_and_owner(account_id, user_id)
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        return account

    async def update(self, user_id: int, account_id: int, data: AccountUpdate) -> Account:
        account = await self.get(user_id, account_id)
        updates = data.model_dump(exclude_none=True)
        if not updates:
            return account
        return await self.repo.update(account, **updates)

    async def delete(self, user_id: int, account_id: int) -> None:
        account = await self.get(user_id, account_id)
        await self.repo.delete(account)

    async def get_balance(self, user_id: int, account_id: int) -> BalanceResponse:
        account = await self.get(user_id, account_id)
        balance = await self.tx_repo.get_balance_for_account(account_id)
        return BalanceResponse(
            account_id=account.id,
            account_name=account.name,
            currency=account.currency,
            balance=balance,
        )
