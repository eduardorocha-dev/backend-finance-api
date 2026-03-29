from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.transaction import Transaction, TransactionType
from app.repositories.account import AccountRepository
from app.repositories.budget import BudgetRepository
from app.repositories.category import CategoryRepository
from app.repositories.transaction import TransactionRepository
from app.schemas.transaction import TransactionCreate, TransactionFilter, TransactionUpdate

_ALERT_THRESHOLD = 0.80


class TransactionService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = TransactionRepository(session)
        self.account_repo = AccountRepository(session)
        self.cat_repo = CategoryRepository(session)
        self.budget_repo = BudgetRepository(session)

    async def list(self, user_id: int, filters: TransactionFilter) -> list[Transaction]:
        return await self.repo.get_all_by_owner(user_id, filters)

    async def create(self, user_id: int, data: TransactionCreate) -> Transaction:
        account = await self.account_repo.get_by_id_and_owner(data.account_id, user_id)
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

        category = await self.cat_repo.get_by_id_and_owner(data.category_id, user_id)
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        transaction = await self.repo.create(
            account_id=data.account_id,
            category_id=data.category_id,
            type=data.type,
            amount=data.amount,
            description=data.description,
            date=data.date,
        )

        if data.type == TransactionType.EXPENSE:
            await self._check_budget_alert(user_id, data.category_id, category.name, data.date.date())

        return transaction

    async def get(self, user_id: int, transaction_id: int) -> Transaction:
        transaction = await self.repo.get_by_id_and_owner(transaction_id, user_id)
        if transaction is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        return transaction

    async def update(self, user_id: int, transaction_id: int, data: TransactionUpdate) -> Transaction:
        transaction = await self.get(user_id, transaction_id)

        if data.category_id is not None:
            category = await self.cat_repo.get_by_id_and_owner(data.category_id, user_id)
            if category is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        updates = data.model_dump(exclude_none=True)
        if not updates:
            return transaction
        return await self.repo.update(transaction, **updates)

    async def delete(self, user_id: int, transaction_id: int) -> None:
        """Soft-delete — financial records are never physically removed."""
        transaction = await self.get(user_id, transaction_id)
        await self.repo.soft_delete(transaction)

    async def _check_budget_alert(
        self, user_id: int, category_id: int, category_name: str, tx_date: date
    ) -> None:
        month = tx_date.replace(day=1)
        budget = await self.budget_repo.get_by_category_and_month(user_id, category_id, month)
        if budget is None:
            return

        spent = await self.repo.get_spending_by_category_for_month(user_id, category_id, month)
        usage_pct = float(spent / budget.limit_amount) if budget.limit_amount else 0.0

        if usage_pct >= _ALERT_THRESHOLD:
            from app.workers.tasks import send_budget_alert
            send_budget_alert.delay(user_id, category_name, round(usage_pct * 100, 1))
