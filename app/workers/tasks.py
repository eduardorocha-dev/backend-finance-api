from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import TYPE_CHECKING, cast

from sqlalchemy import select

# Import all models so SQLAlchemy can resolve relationships before any query runs
import app.models.account  # noqa: F401
import app.models.budget  # noqa: F401
import app.models.category  # noqa: F401
import app.models.exchange_rate  # noqa: F401
import app.models.export  # noqa: F401
import app.models.recurring_transaction  # noqa: F401
import app.models.transaction  # noqa: F401
import app.models.user  # noqa: F401
from app.workers.celery_app import celery_app

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_session():
    """Return a new synchronous DB session for use inside a task."""
    from app.db.sync_session import SyncSessionLocal

    return SyncSessionLocal()


def _claim_budget_alert(
    session: Session, owner_id: int, category_id: int, month: date
) -> tuple[str, float] | None:
    """Sync counterpart of TransactionService._check_budget_alert for worker-created expenses.

    If the category's budget for `month` is at or past the threshold and its alert
    hasn't been sent, marks it sent and returns (category_name, usage_pct) for the
    caller to dispatch after committing. Returns None otherwise.
    """
    from sqlalchemy import CursorResult, func, update

    from app.models.account import Account
    from app.models.budget import ALERT_THRESHOLD, Budget
    from app.models.category import Category
    from app.models.transaction import Transaction, TransactionType
    from app.repositories.base import _month_range

    budget = session.execute(
        select(Budget).where(
            Budget.owner_id == owner_id,
            Budget.category_id == category_id,
            Budget.month == month,
        )
    ).scalar_one_or_none()
    if budget is None or budget.alert_sent_at is not None or not budget.limit_amount:
        return None

    start, end = _month_range(month)
    spent = session.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .join(Account, Transaction.account_id == Account.id)
        .where(
            Account.owner_id == owner_id,
            Transaction.category_id == category_id,
            Transaction.is_deleted == False,  # noqa: E712
            Transaction.type == TransactionType.EXPENSE,
            Transaction.date >= start,
            Transaction.date < end,
        )
    ).scalar_one()
    usage_pct = float(spent / budget.limit_amount)
    if usage_pct < ALERT_THRESHOLD:
        return None

    claimed = cast(
        CursorResult,
        session.execute(
            update(Budget)
            .where(Budget.id == budget.id, Budget.alert_sent_at.is_(None))
            .values(alert_sent_at=func.now())
        ),
    )
    if claimed.rowcount != 1:  # another request sent it first
        return None
    category = session.get(Category, category_id)
    category_name = category.name if category is not None else "Unknown category"
    return category_name, round(usage_pct * 100, 1)


# ── Event-driven tasks ────────────────────────────────────────────────────────


@celery_app.task(name="app.workers.tasks.send_budget_alert")
def send_budget_alert(user_id: int, category_name: str, usage_pct: float) -> None:
    """Notify the user when a category budget reaches the 80% threshold."""
    from app.models.user import User
    from app.utils.email import send_email

    with _get_session() as session:
        user = session.get(User, user_id)
        if user is None or not user.is_active:
            return

    subject = f"Budget alert: {category_name} is at {usage_pct:.1f}%"
    body = (
        f"Hi {user.full_name},\n\n"
        f"You have used {usage_pct:.1f}% of your monthly budget for '{category_name}'.\n"
        "Consider reviewing your spending to stay within your limit.\n\n"
        "— fintrack"
    )
    send_email(user.email, subject, body)
    logger.info(
        "Budget alert sent to user=%s category=%s usage=%.1f%%",
        user_id,
        category_name,
        usage_pct,
    )


@celery_app.task(name="app.workers.tasks.generate_export", bind=True, max_retries=3)
def generate_export(self, export_job_id: int) -> None:
    """Generate a CSV or PDF export file and update the ExportJob record."""
    from app.models.export import ExportFormat, ExportJob, ExportStatus
    from app.utils.export import generate_csv, generate_pdf

    with _get_session() as session:
        export_job = session.get(ExportJob, export_job_id)
        if export_job is None:
            logger.error("ExportJob %s not found", export_job_id)
            return

        export_job.status = ExportStatus.PROCESSING
        session.commit()

        try:
            if export_job.format == ExportFormat.CSV:
                file_path = generate_csv(
                    session,
                    export_job.owner_id,
                    export_job.date_from,
                    export_job.date_to,
                )
            else:
                file_path = generate_pdf(
                    session,
                    export_job.owner_id,
                    export_job.date_from,
                    export_job.date_to,
                )

            export_job.status = ExportStatus.DONE
            export_job.file_url = file_path
            session.commit()
            logger.info("Export job %s completed: %s", export_job_id, file_path)

        except Exception as exc:
            session.rollback()  # the error may have left the transaction unusable
            if self.request.retries >= self.max_retries:
                export_job.status = ExportStatus.FAILED
                session.commit()
                logger.exception("Export job %s failed after all retries", export_job_id)
                raise

            # A retry is scheduled, so the export isn't failed yet: show it as queued again.
            export_job.status = ExportStatus.PENDING
            session.commit()
            logger.warning(
                "Export job %s failed (attempt %d of %d), retrying in 60s",
                export_job_id,
                self.request.retries + 1,
                self.max_retries + 1,
                exc_info=True,
            )
            raise self.retry(exc=exc, countdown=60)


# ── Scheduled tasks (Celery Beat) ─────────────────────────────────────────────


@celery_app.task(name="app.workers.tasks.reset_monthly_budgets")
def reset_monthly_budgets() -> None:
    """Carry over budgets from last month into the current month.

    For each budget from the previous month that does not already have
    a matching budget in the current month, a new one is created with
    the same limit_amount. This means recurring budgets auto-renew.
    """
    from app.models.budget import Budget

    today = date.today()
    current_month = today.replace(day=1)
    last_month_end = current_month - timedelta(days=1)
    last_month = last_month_end.replace(day=1)

    with _get_session() as session:
        last_month_budgets = (
            session.execute(select(Budget).where(Budget.month == last_month)).scalars().all()
        )

        created = 0
        for budget in last_month_budgets:
            existing = session.execute(
                select(Budget).where(
                    Budget.owner_id == budget.owner_id,
                    Budget.category_id == budget.category_id,
                    Budget.month == current_month,
                )
            ).scalar_one_or_none()

            if existing is None:
                session.add(
                    Budget(
                        owner_id=budget.owner_id,
                        category_id=budget.category_id,
                        limit_amount=budget.limit_amount,
                        month=current_month,
                    )
                )
                created += 1

        session.commit()
    logger.info("reset_monthly_budgets: created %d budgets for %s", created, current_month)


@celery_app.task(name="app.workers.tasks.send_weekly_summaries")
def send_weekly_summaries() -> None:
    """Email each active user a summary of their spending over the past 7 days."""
    from app.models.account import Account
    from app.models.transaction import Transaction, TransactionType
    from app.models.user import User
    from app.utils.email import send_email

    today = date.today()
    week_ago = today - timedelta(days=7)

    with _get_session() as session:
        users = (
            session.execute(
                select(User).where(User.is_active == True)  # noqa: E712
            )
            .scalars()
            .all()
        )

        for user in users:
            rows = (
                session.execute(
                    select(Transaction)
                    .join(Account, Transaction.account_id == Account.id)
                    .where(
                        Account.owner_id == user.id,
                        Transaction.is_deleted == False,  # noqa: E712
                        Transaction.date >= week_ago,
                        Transaction.date < today + timedelta(days=1),
                    )
                    .order_by(Transaction.date.desc())
                )
                .scalars()
                .all()
            )

            if not rows:
                continue

            income = sum(t.amount for t in rows if t.type == TransactionType.INCOME)
            expenses = sum(t.amount for t in rows if t.type == TransactionType.EXPENSE)
            net = income - expenses

            subject = f"Your weekly spending summary ({week_ago} → {today})"
            body = (
                f"Hi {user.full_name},\n\n"
                f"Here's your spending summary for the past 7 days:\n\n"
                f"  Income:   ${income:,.2f}\n"
                f"  Expenses: ${expenses:,.2f}\n"
                f"  Net:      ${net:,.2f}\n\n"
                f"  Transactions: {len(rows)}\n\n"
                "Log in to fintrack to see the full breakdown.\n\n"
                "— fintrack"
            )
            send_email(user.email, subject, body)

    logger.info("send_weekly_summaries: processed %d users", len(users))


@celery_app.task(name="app.workers.tasks.snapshot_balances")
def snapshot_balances() -> None:
    """Update balance_snapshot on every account with the current live balance."""
    from sqlalchemy import case, func

    from app.models.account import Account
    from app.models.transaction import Transaction, TransactionType

    with _get_session() as session:
        accounts = session.execute(select(Account)).scalars().all()

        updated = 0
        for account in accounts:
            result = session.execute(
                select(
                    func.coalesce(
                        func.sum(
                            case(
                                (Transaction.type == TransactionType.INCOME, Transaction.amount),
                                else_=-Transaction.amount,
                            )
                        ),
                        0,
                    )
                ).where(
                    Transaction.account_id == account.id,
                    Transaction.is_deleted == False,  # noqa: E712
                )
            ).scalar_one()

            account.balance_snapshot = result
            updated += 1

        session.commit()
    logger.info("snapshot_balances: updated %d accounts", updated)


@celery_app.task(name="app.workers.tasks.process_recurring_transactions")
def process_recurring_transactions() -> None:
    """Create transactions for every active recurring template that is due today or overdue.

    After creating the transaction, the template's next_due_date is advanced by
    one frequency period so it will fire again at the correct time.
    """
    from datetime import date, timedelta

    from dateutil.relativedelta import relativedelta

    from app.models.recurring_transaction import RecurringFrequency, RecurringTransaction
    from app.models.transaction import Transaction, TransactionType

    today = date.today()

    def _advance(rt: RecurringTransaction) -> date:
        if rt.frequency == RecurringFrequency.DAILY:
            return rt.next_due_date + timedelta(days=1)
        if rt.frequency == RecurringFrequency.WEEKLY:
            return rt.next_due_date + timedelta(weeks=1)
        if rt.frequency == RecurringFrequency.MONTHLY:
            return rt.next_due_date + relativedelta(months=1)
        return rt.next_due_date + relativedelta(years=1)

    with _get_session() as session:
        due = (
            session.execute(
                select(RecurringTransaction).where(
                    RecurringTransaction.is_active == True,  # noqa: E712
                    RecurringTransaction.next_due_date <= today,
                )
            )
            .scalars()
            .all()
        )

        created = 0
        alerts: list[tuple[int, str, float]] = []
        for rt in due:
            from datetime import datetime, timezone

            session.add(
                Transaction(
                    account_id=rt.account_id,
                    category_id=rt.category_id,
                    type=rt.type,
                    amount=rt.amount,
                    description=rt.description,
                    date=datetime.combine(rt.next_due_date, datetime.min.time()).replace(
                        tzinfo=timezone.utc
                    ),
                )
            )
            if rt.type == TransactionType.EXPENSE:
                session.flush()  # so the new expense counts towards the budget
                alert = _claim_budget_alert(
                    session, rt.owner_id, rt.category_id, rt.next_due_date.replace(day=1)
                )
                if alert is not None:
                    alerts.append((rt.owner_id, *alert))
            rt.next_due_date = _advance(rt)
            created += 1

        session.commit()

    # Dispatch only after the commit, so an alert is never sent for rolled-back data.
    for owner_id, category_name, usage_pct in alerts:
        send_budget_alert.delay(owner_id, category_name, usage_pct)
    logger.info("process_recurring_transactions: created %d transactions for %s", created, today)
