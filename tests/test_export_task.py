"""generate_export must not report FAILED while a retry is still scheduled."""

from unittest.mock import patch

import pytest
from celery.exceptions import Retry
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models.export import ExportJob, ExportStatus
from app.workers.tasks import generate_export
from tests.conftest import TEST_DATABASE_URL

sync_engine = create_engine(TEST_DATABASE_URL.replace("+asyncpg", ""))


@pytest.fixture
def sync_session():
    with Session(sync_engine) as session:
        yield session


@pytest.fixture
async def export_job_id(client: AsyncClient) -> int:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "full_name": "Test User", "password": "secret123"},
    )
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "user@example.com", "password": "secret123"}
    )
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
    with patch("app.workers.tasks.generate_export.delay"):
        resp = await client.post(
            "/api/v1/exports",
            json={"format": "csv", "date_from": "2024-03-01", "date_to": "2024-03-31"},
            headers=headers,
        )
    return resp.json()["id"]


def run_attempt(sync_session: Session, export_job_id: int, retries: int) -> None:
    """Run one attempt of the task as if it were retry number `retries`, with the export failing."""
    generate_export.push_request(retries=retries)
    try:
        with (
            patch("app.workers.tasks._get_session", return_value=sync_session),
            patch("app.utils.export.generate_csv", side_effect=RuntimeError("disk full")),
            patch.object(generate_export, "retry", side_effect=Retry()),
        ):
            generate_export.run(export_job_id)
    finally:
        generate_export.pop_request()


def status_of(sync_session: Session, export_job_id: int) -> ExportStatus:
    sync_session.expire_all()
    job = sync_session.get(ExportJob, export_job_id)
    assert job is not None
    return job.status


async def test_failure_with_retries_left_stays_pending(export_job_id: int, sync_session):
    with pytest.raises(Retry):
        run_attempt(sync_session, export_job_id, retries=0)

    assert status_of(sync_session, export_job_id) == ExportStatus.PENDING


async def test_failure_on_last_attempt_is_failed(export_job_id: int, sync_session):
    with pytest.raises(RuntimeError, match="disk full"):
        run_attempt(sync_session, export_job_id, retries=generate_export.max_retries)

    assert status_of(sync_session, export_job_id) == ExportStatus.FAILED
