import pytest
from httpx import AsyncClient

BASE = "/api/v1/exchange-rates"


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "er@example.com", "full_name": "ER User", "password": "secret123"},
    )
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "er@example.com", "password": "secret123"}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
async def rate(client: AsyncClient, auth_headers: dict) -> dict:
    resp = await client.post(
        BASE,
        json={
            "from_currency": "USD",
            "to_currency": "BRL",
            "rate": "5.750000",
            "effective_date": "2024-01-15",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()


# ── Create ────────────────────────────────────────────────────────────────────


async def test_create_rate(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        BASE,
        json={
            "from_currency": "USD",
            "to_currency": "EUR",
            "rate": "0.920000",
            "effective_date": "2024-01-15",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["from_currency"] == "USD"
    assert data["to_currency"] == "EUR"
    assert float(data["rate"]) == pytest.approx(0.92, rel=1e-4)


async def test_create_rate_duplicate_returns_409(client: AsyncClient, auth_headers: dict, rate: dict):
    resp = await client.post(
        BASE,
        json={
            "from_currency": "USD",
            "to_currency": "BRL",
            "rate": "5.80",
            "effective_date": "2024-01-15",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 409


async def test_create_rate_same_currency_returns_422(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        BASE,
        json={
            "from_currency": "USD",
            "to_currency": "USD",
            "rate": "1.0",
            "effective_date": "2024-01-15",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_create_rate_negative_returns_422(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        BASE,
        json={
            "from_currency": "USD",
            "to_currency": "BRL",
            "rate": "-1.0",
            "effective_date": "2024-01-15",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_create_requires_auth(client: AsyncClient):
    resp = await client.post(
        BASE,
        json={
            "from_currency": "USD",
            "to_currency": "BRL",
            "rate": "5.75",
            "effective_date": "2024-01-15",
        },
    )
    assert resp.status_code == 401


# ── Get ───────────────────────────────────────────────────────────────────────


async def test_get_rate(client: AsyncClient, auth_headers: dict, rate: dict):
    resp = await client.get(f"{BASE}/{rate['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == rate["id"]


async def test_get_rate_not_found(client: AsyncClient, auth_headers: dict):
    assert (await client.get(f"{BASE}/9999", headers=auth_headers)).status_code == 404


# ── Latest ────────────────────────────────────────────────────────────────────


async def test_get_latest(client: AsyncClient, auth_headers: dict):
    for date, rate_val in [("2024-01-01", "5.70"), ("2024-02-01", "5.85")]:
        await client.post(
            BASE,
            json={"from_currency": "USD", "to_currency": "BRL", "rate": rate_val, "effective_date": date},
            headers=auth_headers,
        )
    resp = await client.get(
        f"{BASE}/latest", params={"from_currency": "USD", "to_currency": "BRL"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert float(resp.json()["rate"]) == pytest.approx(5.85, rel=1e-4)


async def test_get_latest_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.get(
        f"{BASE}/latest", params={"from_currency": "GBP", "to_currency": "EUR"}, headers=auth_headers
    )
    assert resp.status_code == 404


# ── List ──────────────────────────────────────────────────────────────────────


async def test_list_for_pair(client: AsyncClient, auth_headers: dict):
    for date in ["2024-01-01", "2024-02-01", "2024-03-01"]:
        await client.post(
            BASE,
            json={"from_currency": "USD", "to_currency": "EUR", "rate": "0.92", "effective_date": date},
            headers=auth_headers,
        )
    resp = await client.get(
        BASE, params={"from_currency": "USD", "to_currency": "EUR"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 3


# ── Update ────────────────────────────────────────────────────────────────────


async def test_update_rate(client: AsyncClient, auth_headers: dict, rate: dict):
    resp = await client.patch(
        f"{BASE}/{rate['id']}", json={"rate": "6.00"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert float(resp.json()["rate"]) == pytest.approx(6.0, rel=1e-4)


# ── Delete ────────────────────────────────────────────────────────────────────


async def test_delete_rate(client: AsyncClient, auth_headers: dict, rate: dict):
    resp = await client.delete(f"{BASE}/{rate['id']}", headers=auth_headers)
    assert resp.status_code == 204
    assert (await client.get(f"{BASE}/{rate['id']}", headers=auth_headers)).status_code == 404


# ── Convert ───────────────────────────────────────────────────────────────────


async def test_convert(client: AsyncClient, auth_headers: dict, rate: dict):
    resp = await client.post(
        f"{BASE}/convert",
        json={"from_currency": "USD", "to_currency": "BRL", "amount": "100.00"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert float(data["converted_amount"]) == pytest.approx(575.0, rel=1e-4)
    assert float(data["rate"]) == pytest.approx(5.75, rel=1e-4)


async def test_convert_same_currency(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        f"{BASE}/convert",
        json={"from_currency": "USD", "to_currency": "USD", "amount": "42.00"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert float(data["converted_amount"]) == pytest.approx(42.0, rel=1e-4)
    assert float(data["rate"]) == pytest.approx(1.0, rel=1e-4)


async def test_convert_no_rate_returns_404(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        f"{BASE}/convert",
        json={"from_currency": "GBP", "to_currency": "EUR", "amount": "50.00"},
        headers=auth_headers,
    )
    assert resp.status_code == 404
