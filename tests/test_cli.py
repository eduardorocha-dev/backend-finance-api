import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.cli import main, set_admin
from app.models.user import User
from tests.conftest import TEST_DATABASE_URL

sync_engine = create_engine(TEST_DATABASE_URL.replace("+asyncpg", ""))


@pytest.fixture
def sync_session():
    with Session(sync_engine) as session:
        yield session


async def test_set_admin_promotes_and_revokes(client: AsyncClient, sync_session):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "boss@example.com", "full_name": "Boss", "password": "secret123"},
    )

    assert set_admin(sync_session, "boss@example.com", is_admin=True) is True
    user = sync_session.execute(select(User).where(User.email == "boss@example.com")).scalar_one()
    assert user.is_admin is True

    assert set_admin(sync_session, "boss@example.com", is_admin=False) is True
    sync_session.refresh(user)
    assert user.is_admin is False


async def test_set_admin_unknown_email(sync_session):
    assert set_admin(sync_session, "nobody@example.com", is_admin=True) is False


def test_main_requires_email():
    with pytest.raises(SystemExit):
        main(["make-admin"])
