import pytest
from httpx import AsyncClient

BASE = "/api/v1/categories"


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
async def category(client: AsyncClient, auth_headers: dict) -> dict:
    resp = await client.post(BASE, json={"name": "Food"}, headers=auth_headers)
    assert resp.status_code == 201
    return resp.json()


# ── List ──────────────────────────────────────────────────────────────────────

async def test_list_categories_empty(client: AsyncClient, auth_headers: dict):
    resp = await client.get(BASE, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_categories_returns_own(client: AsyncClient, auth_headers: dict, category: dict):
    resp = await client.get(BASE, headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_list_requires_auth(client: AsyncClient):
    assert (await client.get(BASE)).status_code == 401


# ── Create ────────────────────────────────────────────────────────────────────

async def test_create_category(client: AsyncClient, auth_headers: dict):
    resp = await client.post(BASE, json={"name": "Transport"}, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Transport"
    assert data["parent_id"] is None


async def test_create_subcategory(client: AsyncClient, auth_headers: dict, category: dict):
    resp = await client.post(BASE, json={"name": "Groceries", "parent_id": category["id"]}, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["parent_id"] == category["id"]


async def test_create_subcategory_invalid_parent(client: AsyncClient, auth_headers: dict):
    resp = await client.post(BASE, json={"name": "Sub", "parent_id": 9999}, headers=auth_headers)
    assert resp.status_code == 404


# ── Get ───────────────────────────────────────────────────────────────────────

async def test_get_category(client: AsyncClient, auth_headers: dict, category: dict):
    resp = await client.get(f"{BASE}/{category['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == category["id"]


async def test_get_category_not_found(client: AsyncClient, auth_headers: dict):
    assert (await client.get(f"{BASE}/9999", headers=auth_headers)).status_code == 404


# ── Update ────────────────────────────────────────────────────────────────────

async def test_update_category(client: AsyncClient, auth_headers: dict, category: dict):
    resp = await client.patch(f"{BASE}/{category['id']}", json={"name": "Dining"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Dining"


# ── Delete ────────────────────────────────────────────────────────────────────

async def test_delete_category(client: AsyncClient, auth_headers: dict, category: dict):
    resp = await client.delete(f"{BASE}/{category['id']}", headers=auth_headers)
    assert resp.status_code == 204
    assert (await client.get(f"{BASE}/{category['id']}", headers=auth_headers)).status_code == 404
