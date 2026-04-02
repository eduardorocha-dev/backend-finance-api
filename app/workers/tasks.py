from __future__ import annotations

import logging
from datetime import date, timedelta

from sqlalchemy import select

# Import all models so SQLAlchemy can resolve relationships before any query runs
import app.models.account  # noqa: F401
import app.models.budget  # noqa: F401
import app.models.category  # noqa: F401
import app.models.export  # noqa: F401
import app.models.transaction  # noqa: F401
import app.models.user  # noqa: F401
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_session():
    """Return a new synchronous DB session for use inside a task."""
    from app.db.sync_session import SyncSessionLocal

    return SyncSessionLocal()


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
            export_job.status = ExportStatus.FAILED
            session.commit()
            logger.exception("Export job %s failed", export_job_id)
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
                        Transaction.date <= today,
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
