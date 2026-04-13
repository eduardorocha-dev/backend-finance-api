"""Celery Beat periodic schedule definitions."""

from celery.schedules import crontab

BEAT_SCHEDULE = {
    # Resets monthly spend counters — runs 1st of every month at 00:00
    "reset-monthly-budgets": {
        "task": "app.workers.tasks.reset_monthly_budgets",
        "schedule": crontab(hour=0, minute=0, day_of_month="1"),
    },
    # Emails each user a weekly spending summary — every Monday at 08:00
    "send-weekly-summaries": {
        "task": "app.workers.tasks.send_weekly_summaries",
        "schedule": crontab(hour=8, minute=0, day_of_week="monday"),
    },
    # Caches account balances for fast lookups — every day at 23:59
    "snapshot-balances": {
        "task": "app.workers.tasks.snapshot_balances",
        "schedule": crontab(hour=23, minute=59),
    },
    # Fires due recurring transaction templates — every day at 00:05
    "process-recurring-transactions": {
        "task": "app.workers.tasks.process_recurring_transactions",
        "schedule": crontab(hour=0, minute=5),
    },
}