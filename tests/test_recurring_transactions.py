import pytest
from httpx import AsyncClient

BASE = "/api/v1/recurring-transactions"


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "rt@example.com", "full_name": "RT User", "password": "secret123"},
    )
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "rt@example.com", "password": "secret123"}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
async def account_id(client: AsyncClient, auth_headers: dict) -> int:
    resp = await client.post(
        "/api/v1/accounts",
        json={"name": "Checking", "type": "checking", "currency": "USD"},
        headers=auth_headers,
    )
    return resp.json()["id"]


@pytest.fixture
async def category_id(client: AsyncClient, auth_headers: dict) -> int:
    resp = await client.post(
        "/api/v1/categories",
        json={"name": "Rent"},
        headers=auth_headers,
    )
    return resp.json()["id"]


@pytest.fixture
async def recurring(
    client: AsyncClient, auth_headers: dict, account_id: int, category_id: int
) -> dict:
    resp = await client.post(
        BASE,
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "expense",
            "amount": "1500.00",
            "description": "Monthly rent",
            "frequency": "monthly",
            "next_due_date": "2024-02-01",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()


# ── Create ────────────────────────────────────────────────────────────────────


async def test_create_recurring(
    client: AsyncClient, auth_headers: dict, account_id: int, category_id: int
):
    resp = await client.post(
        BASE,
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "income",
            "amount": "3000.00",
            "description": "Salary",
            "frequency": "monthly",
            "next_due_date": "2024-02-05",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["type"] == "income"
    assert float(data["amount"]) == pytest.approx(3000.0)
    assert data["frequency"] == "monthly"
    assert data["is_active"] is True


async def test_create_requires_auth(client: AsyncClient, account_id: int, category_id: int):
    resp = await client.post(
        BASE,
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "expense",
            "amount": "100.00",
            "frequency": "weekly",
            "next_due_date": "2024-02-01",
        },
    )
    assert resp.status_code == 401


async def test_create_negative_amount_returns_422(
    client: AsyncClient, auth_headers: dict, account_id: int, category_id: int
):
    resp = await client.post(
        BASE,
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "expense",
            "amount": "-50.00",
            "frequency": "weekly",
            "next_due_date": "2024-02-01",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


# ── List ──────────────────────────────────────────────────────────────────────


async def test_list_empty(client: AsyncClient, auth_headers: dict):
    resp = await client.get(BASE, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_returns_own(client: AsyncClient, auth_headers: dict, recurring: dict):
    resp = await client.get(BASE, headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["id"] == recurring["id"]


# ── Get ───────────────────────────────────────────────────────────────────────


async def test_get_recurring(client: AsyncClient, auth_headers: dict, recurring: dict):
    resp = await client.get(f"{BASE}/{recurring['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["description"] == "Monthly rent"


async def test_get_not_found(client: AsyncClient, auth_headers: dict):
    assert (await client.get(f"{BASE}/9999", headers=auth_headers)).status_code == 404


# ── Update ────────────────────────────────────────────────────────────────────


async def test_update_amount(client: AsyncClient, auth_headers: dict, recurring: dict):
    resp = await client.patch(
        f"{BASE}/{recurring['id']}", json={"amount": "1600.00"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert float(resp.json()["amount"]) == pytest.approx(1600.0)


async def test_deactivate(client: AsyncClient, auth_headers: dict, recurring: dict):
    resp = await client.patch(
        f"{BASE}/{recurring['id']}", json={"is_active": False}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


async def test_update_frequency(client: AsyncClient, auth_headers: dict, recurring: dict):
    resp = await client.patch(
        f"{BASE}/{recurring['id']}", json={"frequency": "weekly"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["frequency"] == "weekly"


# ── Delete ────────────────────────────────────────────────────────────────────


async def test_delete_recurring(client: AsyncClient, auth_headers: dict, recurring: dict):
    resp = await client.delete(f"{BASE}/{recurring['id']}", headers=auth_headers)
    assert resp.status_code == 204
    assert (await client.get(f"{BASE}/{recurring['id']}", headers=auth_headers)).status_code == 404


# ── Isolation ─────────────────────────────────────────────────────────────────


async def test_other_user_cannot_access(
    client: AsyncClient, auth_headers: dict, recurring: dict
):
    # Register a second user
    await client.post(
        "/api/v1/auth/register",
        json={"email": "other@example.com", "full_name": "Other User", "password": "secret123"},
    )
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "other@example.com", "password": "secret123"}
    )
    other_headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

    assert (
        await client.get(f"{BASE}/{recurring['id']}", headers=other_headers)
    ).status_code == 404
