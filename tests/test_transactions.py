import pytest
from httpx import AsyncClient

BASE = "/api/v1/transactions"


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict:
    await client.post("/api/v1/auth/register", json={
        "email": "user@example.com", "full_name": "Test User", "password": "secret123"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "user@example.com", "password": "secret123"
    })
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
async def account(client: AsyncClient, auth_headers: dict) -> dict:
    resp = await client.post("/api/v1/accounts", json={"name": "Checking", "type": "checking"}, headers=auth_headers)
    return resp.json()


@pytest.fixture
async def category(client: AsyncClient, auth_headers: dict) -> dict:
    resp = await client.post("/api/v1/categories", json={"name": "Food"}, headers=auth_headers)
    return resp.json()


@pytest.fixture
async def transaction(client: AsyncClient, auth_headers: dict, account: dict, category: dict) -> dict:
    resp = await client.post(BASE, json={
        "account_id": account["id"],
        "category_id": category["id"],
        "type": "expense",
        "amount": "50.00",
        "date": "2024-03-15T10:00:00Z",
    }, headers=auth_headers)
    assert resp.status_code == 201
    return resp.json()


# ── List ──────────────────────────────────────────────────────────────────────

async def test_list_transactions_empty(client: AsyncClient, auth_headers: dict):
    resp = await client.get(BASE, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_transactions(client: AsyncClient, auth_headers: dict, transaction: dict):
    resp = await client.get(BASE, headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_list_requires_auth(client: AsyncClient):
    assert (await client.get(BASE)).status_code == 401


# ── Create ────────────────────────────────────────────────────────────────────

async def test_create_transaction(client: AsyncClient, auth_headers: dict, account: dict, category: dict):
    resp = await client.post(BASE, json={
        "account_id": account["id"],
        "category_id": category["id"],
        "type": "income",
        "amount": "1000.00",
        "date": "2024-03-01T00:00:00Z",
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["amount"] == "1000.00"
    assert data["type"] == "income"
    assert data["is_deleted"] is False


async def test_create_transaction_invalid_amount(client: AsyncClient, auth_headers: dict, account: dict, category: dict):
    resp = await client.post(BASE, json={
        "account_id": account["id"],
        "category_id": category["id"],
        "type": "expense",
        "amount": "-10.00",
        "date": "2024-03-01T00:00:00Z",
    }, headers=auth_headers)
    assert resp.status_code == 422


async def test_create_transaction_unknown_account(client: AsyncClient, auth_headers: dict, category: dict):
    resp = await client.post(BASE, json={
        "account_id": 9999,
        "category_id": category["id"],
        "type": "expense",
        "amount": "10.00",
        "date": "2024-03-01T00:00:00Z",
    }, headers=auth_headers)
    assert resp.status_code == 404


# ── Get ───────────────────────────────────────────────────────────────────────

async def test_get_transaction(client: AsyncClient, auth_headers: dict, transaction: dict):
    resp = await client.get(f"{BASE}/{transaction['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == transaction["id"]


async def test_get_transaction_not_found(client: AsyncClient, auth_headers: dict):
    assert (await client.get(f"{BASE}/9999", headers=auth_headers)).status_code == 404


# ── Update ────────────────────────────────────────────────────────────────────

async def test_update_transaction_description(client: AsyncClient, auth_headers: dict, transaction: dict):
    resp = await client.patch(f"{BASE}/{transaction['id']}", json={"description": "Weekly groceries"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["description"] == "Weekly groceries"


# ── Delete (soft) ─────────────────────────────────────────────────────────────

async def test_delete_transaction(client: AsyncClient, auth_headers: dict, transaction: dict):
    resp = await client.delete(f"{BASE}/{transaction['id']}", headers=auth_headers)
    assert resp.status_code == 204
    # Soft-deleted records no longer appear in list or get
    assert (await client.get(f"{BASE}/{transaction['id']}", headers=auth_headers)).status_code == 404
