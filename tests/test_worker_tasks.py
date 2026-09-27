"""Scheduled and event-driven Celery tasks, run directly as functions against the test DB."""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.budget import Budget
from app.workers.tasks import reset_monthly_budgets, send_budget_alert, snapshot_balances


@pytest.fixture
async def headers(client: AsyncClient) -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "full_name": "Test User", "password": "secret123"},
    )
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "user@example.com", "password": "secret123"}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def create(client: AsyncClient, headers: dict, path: str, **body) -> dict:
    resp = await client.post(f"/api/v1/{path}", json=body, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


class FakeDate(date):
    @classmethod
    def today(cls) -> date:
        return date(2024, 3, 10)


# ── send_budget_alert ─────────────────────────────────────────────────────────


async def test_send_budget_alert_emails_the_user(headers: dict, sync_session: Session):
    with (
        patch("app.workers.tasks._get_session", return_value=sync_session),
        patch("app.utils.email.send_email") as send_email,
    ):
        send_budget_alert.run(1, "Food", 85.0)

    to, subject, body = send_email.call_args.args
    assert to == "user@example.com"
    assert subject == "Budget alert: Food is at 85.0%"
    assert "85.0% of your monthly budget for 'Food'" in body


def test_send_budget_alert_unknown_user_is_skipped(sync_session: Session):
    with (
        patch("app.workers.tasks._get_session", return_value=sync_session),
        patch("app.utils.email.send_email") as send_email,
    ):
        send_budget_alert.run(999, "Food", 85.0)

    send_email.assert_not_called()


# ── reset_monthly_budgets ─────────────────────────────────────────────────────


async def test_reset_monthly_budgets_carries_last_month_forward(
    client: AsyncClient, headers: dict, sync_session: Session
):
    food = await create(client, headers, "categories", name="Food")
    rent = await create(client, headers, "categories", name="Rent")
    for category_id, limit in [(food["id"], "100.00"), (rent["id"], "900.00")]:
        await create(
            client,
            headers,
            "budgets",
            category_id=category_id,
            limit_amount=limit,
            month="2024-02-01",
        )
    # Rent already has a March budget with a different limit; it must not be duplicated.
    await create(
        client,
        headers,
        "budgets",
        category_id=rent["id"],
        limit_amount="950.00",
        month="2024-03-01",
    )

    with (
        patch("app.workers.tasks._get_session", return_value=sync_session),
        patch("app.workers.tasks.date", FakeDate),
    ):
        reset_monthly_budgets.run()

    sync_session.expire_all()
    march = sync_session.execute(
        select(Budget.category_id, Budget.limit_amount).where(Budget.month == date(2024, 3, 1))
    ).all()
    assert sorted(march) == sorted(
        [(food["id"], Decimal("100.00")), (rent["id"], Decimal("950.00"))]
    )


# ── snapshot_balances ─────────────────────────────────────────────────────────


async def test_snapshot_balances_stores_live_balance(
    client: AsyncClient, headers: dict, sync_session: Session
):
    account = await create(client, headers, "accounts", name="Checking", type="checking")
    category = await create(client, headers, "categories", name="General")
    tx = {
        "account_id": account["id"],
        "category_id": category["id"],
        "date": "2024-03-05T12:00:00Z",
    }
    await create(client, headers, "transactions", **tx, type="income", amount="100.00")
    await create(client, headers, "transactions", **tx, type="expense", amount="30.00")
    deleted = await create(client, headers, "transactions", **tx, type="expense", amount="10.00")
    await client.delete(f"/api/v1/transactions/{deleted['id']}", headers=headers)

    with patch("app.workers.tasks._get_session", return_value=sync_session):
        snapshot_balances.run()

    sync_session.expire_all()
    snapshot = sync_session.get(Account, account["id"])
    assert snapshot is not None
    assert snapshot.balance_snapshot == Decimal("70.00")  # deleted expense ignored
