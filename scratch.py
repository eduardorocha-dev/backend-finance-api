"""
Scratch script to smoke-test all repositories against a real PostgreSQL instance.

Prerequisites:
    docker compose up -d
    alembic upgrade head

Run:
    python scratch.py
"""

import asyncio
from datetime import date, datetime, timezone

from app.db.session import AsyncSessionLocal
from app.models.account import AccountType, CurrencyCode
from app.models.export import ExportFormat, ExportStatus
from app.models.transaction import TransactionType
from app.repositories import (
    AccountRepository,
    BudgetRepository,
    CategoryRepository,
    ExportRepository,
    TransactionRepository,
    UserRepository,
)
from app.schemas.transaction import TransactionFilter

# ── helpers ───────────────────────────────────────────────────────────────────

OK = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"


def check(label: str, condition: bool) -> None:
    print(f"  {OK if condition else FAIL}  {label}")
    if not condition:
        raise AssertionError(f"FAILED: {label}")


# ── main ──────────────────────────────────────────────────────────────────────


async def main() -> None:
    async with AsyncSessionLocal() as session:
        # ── Users ─────────────────────────────────────────────────────────────
        print("\n── UserRepository ──")
        user_repo = UserRepository(session)

        user = await user_repo.create(
            email="scratch@example.com",
            full_name="Scratch User",
            hashed_password="notreallyhashed",
        )
        check("create user", user.id is not None)
        check("email matches", user.email == "scratch@example.com")

        fetched = await user_repo.get_by_email("scratch@example.com")
        check("get_by_email", fetched is not None and fetched.id == user.id)

        fetched_by_id = await user_repo.get_by_id(user.id)
        check("get_by_id", fetched_by_id is not None and fetched_by_id.id == user.id)

        updated = await user_repo.update(user, full_name="Updated Name")
        check("update full_name", updated.full_name == "Updated Name")

        # ── Categories ────────────────────────────────────────────────────────
        print("\n── CategoryRepository ──")
        cat_repo = CategoryRepository(session)

        category = await cat_repo.create(name="Food", owner_id=user.id)
        check("create category", category.id is not None)

        cats = await cat_repo.get_all_by_owner(user.id)
        check("get_all_by_owner", any(c.id == category.id for c in cats))

        cat_by_owner = await cat_repo.get_by_id_and_owner(category.id, user.id)
        check("get_by_id_and_owner", cat_by_owner is not None)

        updated_cat = await cat_repo.update(category, name="Groceries")
        check("update category name", updated_cat.name == "Groceries")

        # ── Accounts ──────────────────────────────────────────────────────────
        print("\n── AccountRepository ──")
        acc_repo = AccountRepository(session)

        account = await acc_repo.create(
            name="Main Checking",
            type=AccountType.CHECKING,
            currency=CurrencyCode.USD,
            owner_id=user.id,
        )
        check("create account", account.id is not None)

        accounts = await acc_repo.get_all_by_owner(user.id)
        check("get_all_by_owner", any(a.id == account.id for a in accounts))

        acc = await acc_repo.get_by_id_and_owner(account.id, user.id)
        check("get_by_id_and_owner", acc is not None)

        updated_acc = await acc_repo.update(account, name="Renamed Checking")
        check("update account name", updated_acc.name == "Renamed Checking")

        updated_snap = await acc_repo.update_balance_snapshot(account, 1500)
        check("update_balance_snapshot", updated_snap.balance_snapshot == 1500)

        # ── Transactions ──────────────────────────────────────────────────────
        print("\n── TransactionRepository ──")
        tx_repo = TransactionRepository(session)

        now = datetime(2025, 3, 15, 12, 0, tzinfo=timezone.utc)
        tx = await tx_repo.create(
            account_id=account.id,
            category_id=category.id,
            type=TransactionType.EXPENSE,
            amount=120,
            description="Supermarket",
            date=now,
        )
        check("create transaction", tx.id is not None)

        filters = TransactionFilter()
        txs = await tx_repo.get_all_by_owner(user.id, filters)
        check("get_all_by_owner (no filters)", any(t.id == tx.id for t in txs))

        filters_typed = TransactionFilter(type=TransactionType.EXPENSE)
        txs_typed = await tx_repo.get_all_by_owner(user.id, filters_typed)
        check(
            "get_all_by_owner (type filter)",
            all(t.type == TransactionType.EXPENSE for t in txs_typed),
        )

        tx_fetched = await tx_repo.get_by_id_and_owner(tx.id, user.id)
        check("get_by_id_and_owner", tx_fetched is not None)

        updated_tx = await tx_repo.update(tx, description="Updated description")
        check("update transaction", updated_tx.description == "Updated description")

        # ── Report queries ────────────────────────────────────────────────────
        print("\n── TransactionRepository (report queries) ──")
        month = date(2025, 3, 1)

        summary = await tx_repo.get_monthly_summary(user.id, month)
        check(
            "get_monthly_summary returns keys",
            "total_income" in summary and "total_expenses" in summary,
        )
        check("monthly expense = 120", summary["total_expenses"] == 120)
        check("monthly income = 0", summary["total_income"] == 0)

        breakdown = await tx_repo.get_category_breakdown(user.id, month)
        check("get_category_breakdown returns list", isinstance(breakdown, list))
        check("breakdown has one entry", len(breakdown) == 1)
        check("breakdown category name", breakdown[0]["category_name"] == "Groceries")

        cashflow = await tx_repo.get_cashflow(user.id, date(2025, 3, 1), date(2025, 3, 31))
        check("get_cashflow returns list", isinstance(cashflow, list))
        check("cashflow has one entry", len(cashflow) == 1)
        check("cashflow expenses = 120", cashflow[0]["expenses"] == 120)

        spending = await tx_repo.get_spending_by_category_for_month(user.id, category.id, month)
        check("get_spending_by_category_for_month = 120", spending == 120)

        # ── Soft delete ───────────────────────────────────────────────────────
        print("\n── soft_delete ──")
        deleted_tx = await tx_repo.soft_delete(tx)
        check("is_deleted = True", deleted_tx.is_deleted is True)

        txs_after = await tx_repo.get_all_by_owner(user.id, TransactionFilter())
        check("deleted tx not in list", not any(t.id == tx.id for t in txs_after))

        # ── Budgets ───────────────────────────────────────────────────────────
        print("\n── BudgetRepository ──")
        budget_repo = BudgetRepository(session)

        budget = await budget_repo.create(
            owner_id=user.id,
            category_id=category.id,
            limit_amount=500,
            month=date(2025, 3, 1),
        )
        check("create budget", budget.id is not None)

        budgets = await budget_repo.get_all_by_owner(user.id)
        check("get_all_by_owner", any(b.id == budget.id for b in budgets))

        b = await budget_repo.get_by_id_and_owner(budget.id, user.id)
        check("get_by_id_and_owner", b is not None)

        b_by_cat = await budget_repo.get_by_category_and_month(
            user.id, category.id, date(2025, 3, 1)
        )
        check("get_by_category_and_month", b_by_cat is not None)

        updated_b = await budget_repo.update(budget, limit_amount=600)
        check("update limit_amount", updated_b.limit_amount == 600)

        usage = await budget_repo.get_usage(user.id, date(2025, 3, 1))
        check("get_usage returns list", isinstance(usage, list))
        # tx was soft-deleted, so spent_amount should be 0
        check("get_usage spent = 0 (tx deleted)", usage[0]["spent_amount"] == 0)

        # ── Exports ───────────────────────────────────────────────────────────
        print("\n── ExportRepository ──")
        export_repo = ExportRepository(session)

        export_job = await export_repo.create(
            owner_id=user.id,
            format=ExportFormat.CSV,
            status=ExportStatus.PENDING,
            date_from=date(2025, 3, 1),
            date_to=date(2025, 3, 31),
        )
        check("create export job", export_job.id is not None)

        exports = await export_repo.get_all_by_owner(user.id)
        check("get_all_by_owner", any(e.id == export_job.id for e in exports))

        e = await export_repo.get_by_id_and_owner(export_job.id, user.id)
        check("get_by_id_and_owner", e is not None)

        updated_e = await export_repo.update_status(
            export_job, ExportStatus.DONE, file_url="https://example.com/export.csv"
        )
        check("update_status to DONE", updated_e.status == ExportStatus.DONE)
        check("file_url set", updated_e.file_url == "https://example.com/export.csv")

        # ── Rollback — keep the DB clean ──────────────────────────────────────
        await session.rollback()
        print("\n\033[92mAll checks passed. Session rolled back — DB is clean.\033[0m\n")


if __name__ == "__main__":
    asyncio.run(main())
