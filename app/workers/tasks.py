from __future__ import annotations

import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.send_budget_alert")
def send_budget_alert(user_id: int, category_name: str, usage_pct: float) -> None:
    """Notify the user when a category budget reaches the 80% threshold."""
    # TODO: wire to FastAPI-Mail when email is configured
    logger.info(
        "Budget alert: user=%s category=%s usage=%.1f%%",
        user_id,
        category_name,
        usage_pct,
    )


@celery_app.task(name="app.workers.tasks.generate_export")
def generate_export(export_job_id: int) -> None:
    """Generate a CSV or PDF export and update ExportJob status."""
    # TODO: implement file generation (CSV / PDF) and upload to S3
    logger.info("Generating export job_id=%s", export_job_id)


@celery_app.task(name="app.workers.tasks.reset_monthly_budgets")
def reset_monthly_budgets() -> None:
    """Reset monthly spend counters — scheduled 1st of each month."""
    logger.info("Resetting monthly budgets")


@celery_app.task(name="app.workers.tasks.send_weekly_summaries")
def send_weekly_summaries() -> None:
    """Email each user a weekly spending summary — scheduled every Monday."""
    logger.info("Sending weekly summaries")


@celery_app.task(name="app.workers.tasks.snapshot_balances")
def snapshot_balances() -> None:
    """Cache account balances for fast lookups — scheduled daily at 23:59."""
    logger.info("Snapshotting account balances")
