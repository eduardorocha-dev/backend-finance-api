"""Finished exports are downloaded through the API and announced by email."""

import csv
import io
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.utils import export
from app.workers.tasks import generate_export

EXPORTS = "/api/v1/exports"


async def login(client: AsyncClient, email: str) -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test User", "password": "secret123"},
    )
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "secret123"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
async def headers(client: AsyncClient) -> dict:
    return await login(client, "user@example.com")


@pytest.fixture
async def books(client: AsyncClient, headers: dict) -> None:
    """One 42.50 EUR expense on 2024-03-05."""
    account = await client.post(
        "/api/v1/accounts",
        json={"name": "Euro card", "type": "credit", "currency": "EUR"},
        headers=headers,
    )
    category = await client.post("/api/v1/categories", json={"name": "Food"}, headers=headers)
    resp = await client.post(
        "/api/v1/transactions",
        json={
            "account_id": account.json()["id"],
            "category_id": category.json()["id"],
            "type": "expense",
            "amount": "42.50",
            "date": "2024-03-05T12:00:00Z",
        },
        headers=headers,
    )
    assert resp.status_code == 201


async def request_export(client: AsyncClient, headers: dict, fmt: str = "csv") -> int:
    with patch("app.workers.tasks.generate_export.delay"):
        resp = await client.post(
            EXPORTS,
            json={"format": fmt, "date_from": "2024-03-01", "date_to": "2024-03-31"},
            headers=headers,
        )
    assert resp.status_code == 202
    return resp.json()["id"]


def run_export(sync_session: Session, export_id: int, exports_dir) -> MagicMock:
    """Run the Celery task inline; returns the mocked send_email."""
    with (
        patch("app.workers.tasks._get_session", return_value=sync_session),
        patch.object(export, "EXPORTS_DIR", str(exports_dir)),
        patch("app.utils.email.send_email") as send_email,
    ):
        generate_export.run(export_id)
    return send_email


# ── Download ──────────────────────────────────────────────────────────────────


async def test_download_finished_csv(
    client: AsyncClient, headers: dict, books, sync_session: Session, tmp_path
):
    export_id = await request_export(client, headers)
    run_export(sync_session, export_id, tmp_path)

    resp = await client.get(f"{EXPORTS}/{export_id}/download", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert f'filename="fintrack-export-{export_id}.csv"' in resp.headers["content-disposition"]
    rows = list(csv.DictReader(io.StringIO(resp.text)))
    assert [(r["amount"], r["currency"]) for r in rows] == [("42.50", "EUR")]


async def test_api_file_url_is_the_download_link_not_a_server_path(
    client: AsyncClient, headers: dict, books, sync_session: Session, tmp_path
):
    export_id = await request_export(client, headers)
    assert (await client.get(f"{EXPORTS}/{export_id}", headers=headers)).json()["file_url"] is None

    run_export(sync_session, export_id, tmp_path)

    data = (await client.get(f"{EXPORTS}/{export_id}", headers=headers)).json()
    assert data["status"] == "done"
    assert data["file_url"] == f"/api/v1/exports/{export_id}/download"
    assert str(tmp_path) not in str(data)


async def test_download_not_ready_is_409(client: AsyncClient, headers: dict):
    export_id = await request_export(client, headers)
    resp = await client.get(f"{EXPORTS}/{export_id}/download", headers=headers)
    assert resp.status_code == 409


async def test_cannot_download_someone_elses_export(
    client: AsyncClient, headers: dict, books, sync_session: Session, tmp_path
):
    export_id = await request_export(client, headers)
    run_export(sync_session, export_id, tmp_path)

    other = await login(client, "other@example.com")
    resp = await client.get(f"{EXPORTS}/{export_id}/download", headers=other)
    assert resp.status_code == 404


async def test_s3_export_redirects_to_a_presigned_url(
    client: AsyncClient, headers: dict, books, sync_session: Session, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "AWS_ACCESS_KEY_ID", "key")
    monkeypatch.setattr(settings, "AWS_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setattr(settings, "AWS_BUCKET_NAME", "fintrack-exports")
    s3 = MagicMock()
    s3.generate_presigned_url.return_value = "https://signed.example/file?sig=abc"

    export_id = await request_export(client, headers)
    with patch("boto3.client", return_value=s3):
        run_export(sync_session, export_id, tmp_path)
        resp = await client.get(
            f"{EXPORTS}/{export_id}/download", headers=headers, follow_redirects=False
        )

    bucket, key = s3.upload_file.call_args.args[1:3]
    assert bucket == "fintrack-exports"
    assert resp.status_code == 307
    assert resp.headers["location"] == "https://signed.example/file?sig=abc"
    params = s3.generate_presigned_url.call_args.kwargs["Params"]
    assert params == {"Bucket": "fintrack-exports", "Key": key}


# ── Email ─────────────────────────────────────────────────────────────────────


async def test_user_is_emailed_the_link_when_export_is_ready(
    client: AsyncClient, headers: dict, books, sync_session: Session, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "APP_BASE_URL", "https://fintrack.example")
    export_id = await request_export(client, headers)

    send_email = run_export(sync_session, export_id, tmp_path)

    to, subject, body = send_email.call_args.args
    assert to == "user@example.com"
    assert "ready" in subject.lower()
    assert f"https://fintrack.example/api/v1/exports/{export_id}/download" in body


async def test_user_is_emailed_when_export_fails_for_good(
    client: AsyncClient, headers: dict, sync_session: Session
):
    export_id = await request_export(client, headers)

    generate_export.push_request(retries=generate_export.max_retries)
    try:
        with (
            patch("app.workers.tasks._get_session", return_value=sync_session),
            patch("app.utils.export.generate_csv", side_effect=RuntimeError("disk full")),
            patch("app.utils.email.send_email") as send_email,
            pytest.raises(RuntimeError),
        ):
            generate_export.run(export_id)
    finally:
        generate_export.pop_request()

    to, subject, _ = send_email.call_args.args
    assert to == "user@example.com"
    assert "failed" in subject.lower()


# ── Currency in the files ─────────────────────────────────────────────────────


async def test_pdf_shows_the_account_currency(
    client: AsyncClient, headers: dict, books, sync_session: Session, tmp_path
):
    export_id = await request_export(client, headers, fmt="pdf")
    with (
        patch("reportlab.platypus.Table") as table,
        patch("reportlab.platypus.SimpleDocTemplate"),
    ):
        run_export(sync_session, export_id, tmp_path)

    rows = table.call_args.args[0]
    assert rows[1][2] == "42.50 EUR"
    assert not any("$" in cell for row in rows for cell in row)


async def test_download_file_deleted_from_disk_is_410(
    client: AsyncClient, headers: dict, books, sync_session: Session, tmp_path
):
    export_id = await request_export(client, headers)
    run_export(sync_session, export_id, tmp_path)
    for f in tmp_path.iterdir():
        f.unlink()

    resp = await client.get(f"{EXPORTS}/{export_id}/download", headers=headers)
    assert resp.status_code == 410


async def test_legacy_public_url_still_redirects(
    client: AsyncClient, headers: dict, sync_session: Session
):
    from app.models.export import ExportJob, ExportStatus

    export_id = await request_export(client, headers)
    job = sync_session.get(ExportJob, export_id)
    assert job is not None
    job.status = ExportStatus.DONE
    job.file_location = "https://old-bucket.s3.amazonaws.com/export_abc.csv"
    sync_session.commit()

    resp = await client.get(
        f"{EXPORTS}/{export_id}/download", headers=headers, follow_redirects=False
    )
    assert resp.status_code == 307
    assert resp.headers["location"] == "https://old-bucket.s3.amazonaws.com/export_abc.csv"
