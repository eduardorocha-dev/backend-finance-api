"""Transfers move money between two of the user's accounts: debit source, credit destination."""

from decimal import Decimal
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models.account import Account
from app.workers.tasks import snapshot_balances

TX = "/api/v1/transactions"


async def login(client: AsyncClient, email: str) -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test User", "password": "secret123"},
    )
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "secret123"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
async def headers(client: AsyncClient) -> dict:
    return await login(client, "user@example.com")


@pytest.fixture
async def setup(client: AsyncClient, headers: dict) -> dict:
    """Checking with 500.00 of income, an empty Savings account, and a category."""

    async def post(path: str, **body) -> dict:
        resp = await client.post(f"/api/v1/{path}", json=body, headers=headers)
        assert resp.status_code == 201, resp.text
        return resp.json()

    checking = await post("accounts", name="Checking", type="checking")
    savings = await post("accounts", name="Savings", type="savings")
    category = await post("categories", name="Moving money")
    await post(
        "transactions",
        account_id=checking["id"],
        category_id=category["id"],
        type="income",
        amount="500.00",
        date="2024-03-01T12:00:00Z",
    )
    return {"checking": checking["id"], "savings": savings["id"], "category": category["id"]}


def transfer(setup: dict, amount: str = "100.00", **overrides) -> dict:
    return {
        "account_id": setup["checking"],
        "to_account_id": setup["savings"],
        "category_id": setup["category"],
        "type": "transfer",
        "amount": amount,
        "date": "2024-03-05T12:00:00Z",
        **overrides,
    }


async def balance(client: AsyncClient, headers: dict, account_id: int) -> Decimal:
    resp = await client.get(f"/api/v1/accounts/{account_id}/balance", headers=headers)
    assert resp.status_code == 200
    return Decimal(resp.json()["balance"])


# ── Balances ──────────────────────────────────────────────────────────────────


async def test_transfer_debits_source_and_credits_destination(
    client: AsyncClient, headers: dict, setup: dict
):
    resp = await client.post(TX, json=transfer(setup), headers=headers)
    assert resp.status_code == 201
    assert resp.json()["to_account_id"] == setup["savings"]

    assert await balance(client, headers, setup["checking"]) == Decimal("400.00")
    assert await balance(client, headers, setup["savings"]) == Decimal("100.00")


async def test_deleting_a_transfer_restores_both_balances(
    client: AsyncClient, headers: dict, setup: dict
):
    tx = (await client.post(TX, json=transfer(setup), headers=headers)).json()
    await client.delete(f"{TX}/{tx['id']}", headers=headers)

    assert await balance(client, headers, setup["checking"]) == Decimal("500.00")
    assert await balance(client, headers, setup["savings"]) == Decimal("0")


async def test_snapshot_includes_incoming_transfers(
    client: AsyncClient, headers: dict, setup: dict, sync_session: Session
):
    await client.post(TX, json=transfer(setup), headers=headers)

    with patch("app.workers.tasks._get_session", return_value=sync_session):
        snapshot_balances.run()

    sync_session.expire_all()
    snapshots = {a.id: a.balance_snapshot for a in sync_session.query(Account).all()}
    assert snapshots[setup["checking"]] == Decimal("400.00")
    assert snapshots[setup["savings"]] == Decimal("100.00")


async def test_filtering_by_destination_account_lists_incoming_transfer(
    client: AsyncClient, headers: dict, setup: dict
):
    tx = (await client.post(TX, json=transfer(setup), headers=headers)).json()

    resp = await client.get(TX, params={"account_id": setup["savings"]}, headers=headers)
    assert [t["id"] for t in resp.json()] == [tx["id"]]


# ── Validation ────────────────────────────────────────────────────────────────


async def test_transfer_requires_destination(client: AsyncClient, headers: dict, setup: dict):
    resp = await client.post(TX, json=transfer(setup, to_account_id=None), headers=headers)
    assert resp.status_code == 422


async def test_only_transfers_have_a_destination(client: AsyncClient, headers: dict, setup: dict):
    resp = await client.post(TX, json=transfer(setup, type="expense"), headers=headers)
    assert resp.status_code == 422


async def test_cannot_transfer_to_the_same_account(client: AsyncClient, headers: dict, setup: dict):
    resp = await client.post(
        TX, json=transfer(setup, to_account_id=setup["checking"]), headers=headers
    )
    assert resp.status_code == 422


async def test_cannot_transfer_to_someone_elses_account(
    client: AsyncClient, headers: dict, setup: dict
):
    other_headers = await login(client, "other@example.com")
    other = await client.post(
        "/api/v1/accounts", json={"name": "Theirs", "type": "checking"}, headers=other_headers
    )

    resp = await client.post(
        TX, json=transfer(setup, to_account_id=other.json()["id"]), headers=headers
    )
    assert resp.status_code == 404
    assert await balance(client, headers, setup["checking"]) == Decimal("500.00")


async def test_cannot_transfer_between_currencies(client: AsyncClient, headers: dict, setup: dict):
    euros = await client.post(
        "/api/v1/accounts",
        json={"name": "Euro account", "type": "savings", "currency": "EUR"},
        headers=headers,
    )

    resp = await client.post(
        TX, json=transfer(setup, to_account_id=euros.json()["id"]), headers=headers
    )
    assert resp.status_code == 422
    assert "different currencies" in resp.json()["detail"]


async def test_recurring_transfers_are_rejected(client: AsyncClient, headers: dict, setup: dict):
    resp = await client.post(
        "/api/v1/recurring-transactions",
        json={
            "account_id": setup["checking"],
            "category_id": setup["category"],
            "type": "transfer",
            "amount": "50.00",
            "frequency": "monthly",
            "next_due_date": "2024-03-01",
        },
        headers=headers,
    )
    assert resp.status_code == 422
