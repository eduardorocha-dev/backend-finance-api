from unittest.mock import patch

import pytest
from httpx import AsyncClient

BASE = "/api/v1/exports"


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


# ── Create ────────────────────────────────────────────────────────────────────


async def test_request_export(client: AsyncClient, auth_headers: dict):
    with patch("app.workers.tasks.generate_export.delay"):
        resp = await client.post(
            BASE,
            json={
                "format": "csv",
                "date_from": "2024-03-01",
                "date_to": "2024-03-31",
            },
            headers=auth_headers,
        )
    assert resp.status_code == 202
    data = resp.json()
    assert data["format"] == "csv"
    assert data["status"] == "pending"
    assert data["file_url"] is None


async def test_request_export_invalid_dates(client: AsyncClient, auth_headers: dict):
    with patch("app.workers.tasks.generate_export.delay"):
        resp = await client.post(
            BASE,
            json={
                "format": "csv",
                "date_from": "2024-03-31",
                "date_to": "2024-03-01",  # before date_from
            },
            headers=auth_headers,
        )
    assert resp.status_code == 422


async def test_request_export_requires_auth(client: AsyncClient):
    resp = await client.post(
        BASE, json={"format": "csv", "date_from": "2024-03-01", "date_to": "2024-03-31"}
    )
    assert resp.status_code == 401


# ── Get status ────────────────────────────────────────────────────────────────


async def test_get_export_status(client: AsyncClient, auth_headers: dict):
    with patch("app.workers.tasks.generate_export.delay"):
        created = (
            await client.post(
                BASE,
                json={
                    "format": "pdf",
                    "date_from": "2024-03-01",
                    "date_to": "2024-03-31",
                },
                headers=auth_headers,
            )
        ).json()

    resp = await client.get(f"{BASE}/{created['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]
    assert resp.json()["status"] == "pending"


async def test_get_export_not_found(client: AsyncClient, auth_headers: dict):
    assert (await client.get(f"{BASE}/9999", headers=auth_headers)).status_code == 404
