from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "fintrack",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
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
    },
)
