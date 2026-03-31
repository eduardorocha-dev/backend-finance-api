import pytest
from httpx import AsyncClient

BASE = "/api/v1/accounts"


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
async def account(client: AsyncClient, auth_headers: dict) -> dict:
    resp = await client.post(
        BASE, json={"name": "Checking", "type": "checking", "currency": "USD"}, headers=auth_headers
    )
    assert resp.status_code == 201
    return resp.json()


# ── List ──────────────────────────────────────────────────────────────────────


async def test_list_accounts_empty(client: AsyncClient, auth_headers: dict):
    resp = await client.get(BASE, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_accounts_returns_own(client: AsyncClient, auth_headers: dict, account: dict):
    resp = await client.get(BASE, headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_list_requires_auth(client: AsyncClient):
    assert (await client.get(BASE)).status_code == 401


# ── Create ────────────────────────────────────────────────────────────────────


async def test_create_account(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        BASE, json={"name": "Savings", "type": "savings", "currency": "BRL"}, headers=auth_headers
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Savings"
    assert data["type"] == "savings"
    assert data["currency"] == "BRL"


# ── Get ───────────────────────────────────────────────────────────────────────


async def test_get_account(client: AsyncClient, auth_headers: dict, account: dict):
    resp = await client.get(f"{BASE}/{account['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == account["id"]


async def test_get_account_not_found(client: AsyncClient, auth_headers: dict):
    assert (await client.get(f"{BASE}/9999", headers=auth_headers)).status_code == 404


# ── Update ────────────────────────────────────────────────────────────────────


async def test_update_account(client: AsyncClient, auth_headers: dict, account: dict):
    resp = await client.patch(
        f"{BASE}/{account['id']}", json={"name": "Main Checking"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Main Checking"


# ── Delete ────────────────────────────────────────────────────────────────────


async def test_delete_account(client: AsyncClient, auth_headers: dict, account: dict):
    resp = await client.delete(f"{BASE}/{account['id']}", headers=auth_headers)
    assert resp.status_code == 204
    assert (await client.get(f"{BASE}/{account['id']}", headers=auth_headers)).status_code == 404


# ── Balance ───────────────────────────────────────────────────────────────────


async def test_get_balance(client: AsyncClient, auth_headers: dict, account: dict):
    resp = await client.get(f"{BASE}/{account['id']}/balance", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["account_id"] == account["id"]
    assert float(data["balance"]) == 0.0
