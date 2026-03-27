import pytest
from httpx import AsyncClient


REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
ME_URL = "/api/v1/auth/me"

USER_PAYLOAD = {
    "email": "test@example.com",
    "full_name": "Test User",
    "password": "secret123",
}


@pytest.fixture
async def registered_user(client: AsyncClient) -> dict:
    response = await client.post(REGISTER_URL, json=USER_PAYLOAD)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
async def auth_headers(client: AsyncClient, registered_user: dict) -> dict:
    response = await client.post(
        LOGIN_URL,
        json={"email": USER_PAYLOAD["email"], "password": USER_PAYLOAD["password"]},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── Register ──────────────────────────────────────────────────────────────────

async def test_register_success(client: AsyncClient):
    response = await client.post(REGISTER_URL, json=USER_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == USER_PAYLOAD["email"]
    assert data["full_name"] == USER_PAYLOAD["full_name"]
    assert data["is_active"] is True
    assert "id" in data


async def test_register_duplicate_email(client: AsyncClient, registered_user: dict):
    response = await client.post(REGISTER_URL, json=USER_PAYLOAD)
    assert response.status_code == 409


async def test_register_invalid_email(client: AsyncClient):
    response = await client.post(
        REGISTER_URL, json={**USER_PAYLOAD, "email": "not-an-email"}
    )
    assert response.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────

async def test_login_success(client: AsyncClient, registered_user: dict):
    response = await client.post(
        LOGIN_URL,
        json={"email": USER_PAYLOAD["email"], "password": USER_PAYLOAD["password"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient, registered_user: dict):
    response = await client.post(
        LOGIN_URL,
        json={"email": USER_PAYLOAD["email"], "password": "wrongpassword"},
    )
    assert response.status_code == 401


async def test_login_unknown_email(client: AsyncClient):
    response = await client.post(
        LOGIN_URL,
        json={"email": "ghost@example.com", "password": "secret123"},
    )
    assert response.status_code == 401


# ── Me ────────────────────────────────────────────────────────────────────────

async def test_me_success(client: AsyncClient, auth_headers: dict):
    response = await client.get(ME_URL, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == USER_PAYLOAD["email"]
    assert data["full_name"] == USER_PAYLOAD["full_name"]


async def test_me_no_token(client: AsyncClient):
    response = await client.get(ME_URL)
    assert response.status_code == 401


async def test_me_invalid_token(client: AsyncClient):
    response = await client.get(ME_URL, headers={"Authorization": "Bearer bad.token.here"})
    assert response.status_code == 401
