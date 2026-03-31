import pytest
from httpx import AsyncClient

BASE = "/api/v1/reports"


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
async def seeded(client: AsyncClient, auth_headers: dict) -> None:
    """Create an account, category, and two transactions for report tests."""
    account = (
        await client.post(
            "/api/v1/accounts", json={"name": "Checking", "type": "checking"}, headers=auth_headers
        )
    ).json()
    category = (
        await client.post("/api/v1/categories", json={"name": "Food"}, headers=auth_headers)
    ).json()

    await client.post(
        "/api/v1/transactions",
        json={
            "account_id": account["id"],
            "category_id": category["id"],
            "type": "income",
            "amount": "1000.00",
            "date": "2024-03-10T00:00:00Z",
        },
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/transactions",
        json={
            "account_id": account["id"],
            "category_id": category["id"],
            "type": "expense",
            "amount": "200.00",
            "date": "2024-03-15T00:00:00Z",
        },
        headers=auth_headers,
    )


# ── Monthly ───────────────────────────────────────────────────────────────────


async def test_monthly_report_empty(client: AsyncClient, auth_headers: dict):
    resp = await client.get(f"{BASE}/monthly", params={"month": "2024-03-01"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert float(data["total_income"]) == 0.0
    assert float(data["total_expenses"]) == 0.0
    assert float(data["net"]) == 0.0


async def test_monthly_report(client: AsyncClient, auth_headers: dict, seeded):
    resp = await client.get(f"{BASE}/monthly", params={"month": "2024-03-01"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_income"] == "1000.00"
    assert data["total_expenses"] == "200.00"
    assert data["net"] == "800.00"


async def test_monthly_requires_auth(client: AsyncClient):
    assert (await client.get(f"{BASE}/monthly", params={"month": "2024-03-01"})).status_code == 401


# ── Category breakdown ────────────────────────────────────────────────────────


async def test_categories_report_empty(client: AsyncClient, auth_headers: dict):
    resp = await client.get(
        f"{BASE}/categories", params={"month": "2024-03-01"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["breakdown"] == []


async def test_categories_report(client: AsyncClient, auth_headers: dict, seeded):
    resp = await client.get(
        f"{BASE}/categories", params={"month": "2024-03-01"}, headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_expenses"] == "200.00"
    assert len(data["breakdown"]) == 1
    assert data["breakdown"][0]["percentage"] == 100.0


# ── Cashflow ──────────────────────────────────────────────────────────────────


async def test_cashflow_report_empty(client: AsyncClient, auth_headers: dict):
    resp = await client.get(
        f"{BASE}/cashflow",
        params={"date_from": "2024-03-01", "date_to": "2024-03-31"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["entries"] == []


async def test_cashflow_report(client: AsyncClient, auth_headers: dict, seeded):
    resp = await client.get(
        f"{BASE}/cashflow",
        params={"date_from": "2024-03-01", "date_to": "2024-03-31"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    entries = resp.json()["entries"]
    assert len(entries) == 2
    nets = {e["period"]: float(e["income"]) - float(e["expenses"]) for e in entries}
    assert nets["2024-03-10"] == 1000.0
    assert nets["2024-03-15"] == -200.0
