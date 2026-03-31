from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction, TransactionType
from app.repositories.base import BaseRepository, _month_range
from app.schemas.transaction import TransactionFilter


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Transaction, session)

    async def get_all_by_owner(
        self, owner_id: int, filters: TransactionFilter
    ) -> list[Transaction]:
        stmt = (
            select(Transaction)
            .join(Account, Transaction.account_id == Account.id)
            .where(
                Account.owner_id == owner_id,
                Transaction.is_deleted == False,  # noqa: E712
            )
        )
        if filters.account_id is not None:
            stmt = stmt.where(Transaction.account_id == filters.account_id)
        if filters.category_id is not None:
            stmt = stmt.where(Transaction.category_id == filters.category_id)
        if filters.type is not None:
            stmt = stmt.where(Transaction.type == filters.type)
        if filters.date_from is not None:
            stmt = stmt.where(Transaction.date >= filters.date_from)
        if filters.date_to is not None:
            stmt = stmt.where(Transaction.date <= filters.date_to)
        stmt = stmt.order_by(Transaction.date.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id_and_owner(self, transaction_id: int, owner_id: int) -> Transaction | None:
        result = await self.session.execute(
            select(Transaction)
            .join(Account, Transaction.account_id == Account.id)
            .where(
                Transaction.id == transaction_id,
                Account.owner_id == owner_id,
                Transaction.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def update(self, transaction: Transaction, **kwargs) -> Transaction:
        for key, value in kwargs.items():
            setattr(transaction, key, value)
        await self.session.flush()
        await self.session.refresh(transaction)
        return transaction

    async def soft_delete(self, transaction: Transaction) -> Transaction:
        transaction.is_deleted = True
        await self.session.flush()
        return transaction

    async def get_monthly_summary(self, owner_id: int, month: date) -> dict:
        start, end = _month_range(month)
        result = await self.session.execute(
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (Transaction.type == TransactionType.INCOME, Transaction.amount),
                            else_=Decimal("0"),
                        )
                    ),
                    Decimal("0"),
                ).label("total_income"),
                func.coalesce(
                    func.sum(
                        case(
                            (Transaction.type == TransactionType.EXPENSE, Transaction.amount),
                            else_=Decimal("0"),
                        )
                    ),
                    Decimal("0"),
                ).label("total_expenses"),
            )
            .join(Account, Transaction.account_id == Account.id)
            .where(
                Account.owner_id == owner_id,
                Transaction.is_deleted == False,  # noqa: E712
                Transaction.date >= start,
                Transaction.date < end,
            )
        )
        row = result.one()
        return {"total_income": row.total_income, "total_expenses": row.total_expenses}

    async def get_category_breakdown(self, owner_id: int, month: date) -> list[dict]:
        start, end = _month_range(month)
        result = await self.session.execute(
            select(
                Category.id.label("category_id"),
                Category.name.label("category_name"),
                func.sum(Transaction.amount).label("total_amount"),
            )
            .join(Account, Transaction.account_id == Account.id)
            .join(Category, Transaction.category_id == Category.id)
            .where(
                Account.owner_id == owner_id,
                Transaction.is_deleted == False,  # noqa: E712
                Transaction.type == TransactionType.EXPENSE,
                Transaction.date >= start,
                Transaction.date < end,
            )
            .group_by(Category.id, Category.name)
            .order_by(func.sum(Transaction.amount).desc())
        )
        return [
            {
                "category_id": row.category_id,
                "category_name": row.category_name,
                "total_amount": row.total_amount,
            }
            for row in result.all()
        ]

    async def get_cashflow(self, owner_id: int, date_from: date, date_to: date) -> list[dict]:
        result = await self.session.execute(
            select(
                func.date(Transaction.date).label("period"),
                func.coalesce(
                    func.sum(
                        case(
                            (Transaction.type == TransactionType.INCOME, Transaction.amount),
                            else_=Decimal("0"),
                        )
                    ),
                    Decimal("0"),
                ).label("income"),
                func.coalesce(
                    func.sum(
                        case(
                            (Transaction.type == TransactionType.EXPENSE, Transaction.amount),
                            else_=Decimal("0"),
                        )
                    ),
                    Decimal("0"),
                ).label("expenses"),
            )
            .join(Account, Transaction.account_id == Account.id)
            .where(
                Account.owner_id == owner_id,
                Transaction.is_deleted == False,  # noqa: E712
                func.date(Transaction.date) >= date_from,
                func.date(Transaction.date) <= date_to,
            )
            .group_by(func.date(Transaction.date))
            .order_by(func.date(Transaction.date))
        )
        return [
            {
                "period": row.period,
                "income": row.income,
                "expenses": row.expenses,
            }
            for row in result.all()
        ]

    async def get_balance_for_account(self, account_id: int) -> Decimal:
        """Live balance: income adds, expenses and transfers subtract."""
        result = await self.session.execute(
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (Transaction.type == TransactionType.INCOME, Transaction.amount),
                            else_=-Transaction.amount,
                        )
                    ),
                    Decimal("0"),
                )
            ).where(
                Transaction.account_id == account_id,
                Transaction.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one()

    async def get_spending_by_category_for_month(
        self, owner_id: int, category_id: int, month: date
    ) -> Decimal:
        start, end = _month_range(month)
        result = await self.session.execute(
            select(func.coalesce(func.sum(Transaction.amount), Decimal("0")))
            .join(Account, Transaction.account_id == Account.id)
            .where(
                Account.owner_id == owner_id,
                Transaction.category_id == category_id,
                Transaction.is_deleted == False,  # noqa: E712
                Transaction.type == TransactionType.EXPENSE,
                Transaction.date >= start,
                Transaction.date < end,
            )
        )
        return result.scalar_one()
