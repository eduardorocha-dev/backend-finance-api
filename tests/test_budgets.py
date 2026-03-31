import pytest
from httpx import AsyncClient

BASE = "/api/v1/budgets"


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
async def category(client: AsyncClient, auth_headers: dict) -> dict:
    resp = await client.post("/api/v1/categories", json={"name": "Food"}, headers=auth_headers)
    return resp.json()


@pytest.fixture
async def budget(client: AsyncClient, auth_headers: dict, category: dict) -> dict:
    resp = await client.post(
        BASE,
        json={
            "category_id": category["id"],
            "limit_amount": "500.00",
            "month": "2024-03-01",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()


# ── List ──────────────────────────────────────────────────────────────────────


async def test_list_budgets_empty(client: AsyncClient, auth_headers: dict):
    resp = await client.get(BASE, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_budgets(client: AsyncClient, auth_headers: dict, budget: dict):
    resp = await client.get(BASE, headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_list_requires_auth(client: AsyncClient):
    assert (await client.get(BASE)).status_code == 401


# ── Create ────────────────────────────────────────────────────────────────────


async def test_create_budget(client: AsyncClient, auth_headers: dict, category: dict):
    resp = await client.post(
        BASE,
        json={
            "category_id": category["id"],
            "limit_amount": "200.00",
            "month": "2024-04-01",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["limit_amount"] == "200.00"
    assert data["month"] == "2024-04-01"


async def test_create_budget_duplicate(
    client: AsyncClient, auth_headers: dict, category: dict, budget: dict
):
    resp = await client.post(
        BASE,
        json={
            "category_id": category["id"],
            "limit_amount": "300.00",
            "month": "2024-03-01",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 409


async def test_create_budget_invalid_month(client: AsyncClient, auth_headers: dict, category: dict):
    resp = await client.post(
        BASE,
        json={
            "category_id": category["id"],
            "limit_amount": "200.00",
            "month": "2024-03-15",  # not the 1st
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_create_budget_unknown_category(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        BASE,
        json={
            "category_id": 9999,
            "limit_amount": "200.00",
            "month": "2024-04-01",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 404


# ── Get ───────────────────────────────────────────────────────────────────────


async def test_get_budget(client: AsyncClient, auth_headers: dict, budget: dict):
    resp = await client.get(f"{BASE}/{budget['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == budget["id"]


async def test_get_budget_not_found(client: AsyncClient, auth_headers: dict):
    assert (await client.get(f"{BASE}/9999", headers=auth_headers)).status_code == 404


# ── Update ────────────────────────────────────────────────────────────────────


async def test_update_budget(client: AsyncClient, auth_headers: dict, budget: dict):
    resp = await client.patch(
        f"{BASE}/{budget['id']}", json={"limit_amount": "750.00"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["limit_amount"] == "750.00"


# ── Delete ────────────────────────────────────────────────────────────────────


async def test_delete_budget(client: AsyncClient, auth_headers: dict, budget: dict):
    resp = await client.delete(f"{BASE}/{budget['id']}", headers=auth_headers)
    assert resp.status_code == 204
    assert (await client.get(f"{BASE}/{budget['id']}", headers=auth_headers)).status_code == 404


# ── Usage ─────────────────────────────────────────────────────────────────────


async def test_get_usage(client: AsyncClient, auth_headers: dict, budget: dict):
    resp = await client.get(f"{BASE}/usage", params={"month": "2024-03-01"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["limit_amount"] == "500.00"
    assert float(data[0]["spent_amount"]) == 0.0
    assert data[0]["alert_triggered"] is False
