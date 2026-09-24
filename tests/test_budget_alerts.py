"""Budget alerts fire once per budget (one category, one month), not on every expense."""

from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.workers.tasks import process_recurring_transactions

DELAY = "app.workers.tasks.send_budget_alert.delay"


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "full_name": "Test User", "password": "secret123"},
    )
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "user@example.com", "password": "secret123"}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
async def setup(client: AsyncClient, auth_headers: dict) -> dict:
    """An account, a Food category and a 100.00 Food budget for March 2024."""
    account = await client.post(
        "/api/v1/accounts", json={"name": "Checking", "type": "checking"}, headers=auth_headers
    )
    category = await client.post("/api/v1/categories", json={"name": "Food"}, headers=auth_headers)
    budget = await client.post(
        "/api/v1/budgets",
        json={
            "category_id": category.json()["id"],
            "limit_amount": "100.00",
            "month": "2024-03-01",
        },
        headers=auth_headers,
    )
    return {
        "account_id": account.json()["id"],
        "category_id": category.json()["id"],
        "budget_id": budget.json()["id"],
    }


async def spend(
    client: AsyncClient,
    headers: dict,
    setup: dict,
    amount: str,
    day: str,
    category_id: int | None = None,
) -> dict:
    resp = await client.post(
        "/api/v1/transactions",
        json={
            "account_id": setup["account_id"],
            "category_id": category_id or setup["category_id"],
            "type": "expense",
            "amount": amount,
            "date": f"{day}T12:00:00Z",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()


async def test_no_alert_below_threshold(client: AsyncClient, auth_headers: dict, setup: dict):
    with patch(DELAY) as delay:
        await spend(client, auth_headers, setup, "79.00", "2024-03-05")
    delay.assert_not_called()


async def test_alert_sent_once_when_threshold_crossed(
    client: AsyncClient, auth_headers: dict, setup: dict
):
    with patch(DELAY) as delay:
        await spend(client, auth_headers, setup, "85.00", "2024-03-05")  # 85%
        await spend(client, auth_headers, setup, "5.00", "2024-03-06")  # 90%
        await spend(client, auth_headers, setup, "20.00", "2024-03-07")  # 110%
    delay.assert_called_once()
    assert delay.call_args.args[1:] == ("Food", 85.0)


async def test_raising_the_limit_rearms_the_alert(
    client: AsyncClient, auth_headers: dict, setup: dict
):
    with patch(DELAY) as delay:
        await spend(client, auth_headers, setup, "85.00", "2024-03-05")
        resp = await client.patch(
            f"/api/v1/budgets/{setup['budget_id']}",
            json={"limit_amount": "200.00"},  # now at 42.5%
            headers=auth_headers,
        )
        assert resp.status_code == 200
        await spend(client, auth_headers, setup, "80.00", "2024-03-06")  # 82.5% of the new limit
    assert delay.call_count == 2


async def test_each_month_alerts_separately(client: AsyncClient, auth_headers: dict, setup: dict):
    await client.post(
        "/api/v1/budgets",
        json={"category_id": setup["category_id"], "limit_amount": "100.00", "month": "2024-04-01"},
        headers=auth_headers,
    )
    with patch(DELAY) as delay:
        await spend(client, auth_headers, setup, "90.00", "2024-03-05")
        await spend(client, auth_headers, setup, "90.00", "2024-04-05")
    assert delay.call_count == 2


# ── Other ways an expense can land in a budget ────────────────────────────────


async def test_recurring_expense_triggers_alert(
    client: AsyncClient, auth_headers: dict, setup: dict, sync_session
):
    resp = await client.post(
        "/api/v1/recurring-transactions",
        json={
            "account_id": setup["account_id"],
            "category_id": setup["category_id"],
            "type": "expense",
            "amount": "90.00",
            "frequency": "monthly",
            "next_due_date": "2024-03-05",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201

    with (
        patch("app.workers.tasks._get_session", return_value=sync_session),
        patch(DELAY) as delay,
    ):
        process_recurring_transactions.run()

    delay.assert_called_once()
    assert delay.call_args.args[1:] == ("Food", 90.0)


async def test_recurring_expense_respects_alert_already_sent(
    client: AsyncClient, auth_headers: dict, setup: dict, sync_session
):
    with patch(DELAY):
        await spend(client, auth_headers, setup, "85.00", "2024-03-01")
    await client.post(
        "/api/v1/recurring-transactions",
        json={
            "account_id": setup["account_id"],
            "category_id": setup["category_id"],
            "type": "expense",
            "amount": "10.00",
            "frequency": "monthly",
            "next_due_date": "2024-03-05",
        },
        headers=auth_headers,
    )

    with (
        patch("app.workers.tasks._get_session", return_value=sync_session),
        patch(DELAY) as delay,
    ):
        process_recurring_transactions.run()

    delay.assert_not_called()


async def test_moving_expense_into_budgeted_category_triggers_alert(
    client: AsyncClient, auth_headers: dict, setup: dict
):
    other = await client.post("/api/v1/categories", json={"name": "Other"}, headers=auth_headers)
    with patch(DELAY) as delay:
        tx = await spend(
            client, auth_headers, setup, "90.00", "2024-03-05", category_id=other.json()["id"]
        )
        delay.assert_not_called()  # "Other" has no budget

        resp = await client.patch(
            f"/api/v1/transactions/{tx['id']}",
            json={"category_id": setup["category_id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
    delay.assert_called_once()


async def test_moving_expense_into_budgeted_month_triggers_alert(
    client: AsyncClient, auth_headers: dict, setup: dict
):
    with patch(DELAY) as delay:
        tx = await spend(client, auth_headers, setup, "90.00", "2024-02-10")  # no Feb budget
        delay.assert_not_called()

        resp = await client.patch(
            f"/api/v1/transactions/{tx['id']}",
            json={"date": "2024-03-10T12:00:00Z"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
    delay.assert_called_once()


async def test_budget_read_shows_when_alert_was_sent(
    client: AsyncClient, auth_headers: dict, setup: dict
):
    url = f"/api/v1/budgets/{setup['budget_id']}"
    assert (await client.get(url, headers=auth_headers)).json()["alert_sent_at"] is None

    with patch(DELAY):
        await spend(client, auth_headers, setup, "90.00", "2024-03-05")

    assert (await client.get(url, headers=auth_headers)).json()["alert_sent_at"] is not None
