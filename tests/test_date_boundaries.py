"""Transactions later in the day on the last day of a date range must be included.

`Transaction.date` is a timestamp, so comparing it with `<= some_date` only
matches up to midnight at the start of that day.
"""

import csv
from datetime import UTC, date, datetime, time
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.utils import export
from app.workers.tasks import send_weekly_summaries


@pytest.fixture
async def owner_with_transaction_at(client: AsyncClient):
    """Return a factory that creates a user with one expense at the given datetime."""

    async def create(when: datetime) -> None:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "user@example.com", "full_name": "Test User", "password": "secret123"},
        )
        resp = await client.post(
            "/api/v1/auth/login", json={"email": "user@example.com", "password": "secret123"}
        )
        headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
        account = await client.post(
            "/api/v1/accounts", json={"name": "Checking", "type": "checking"}, headers=headers
        )
        category = await client.post("/api/v1/categories", json={"name": "Food"}, headers=headers)
        resp = await client.post(
            "/api/v1/transactions",
            json={
                "account_id": account.json()["id"],
                "category_id": category.json()["id"],
                "type": "expense",
                "amount": "42.00",
                "date": when.isoformat(),
            },
            headers=headers,
        )
        assert resp.status_code == 201

    return create


async def test_csv_export_includes_last_day(owner_with_transaction_at, sync_session, tmp_path):
    await owner_with_transaction_at(datetime(2024, 3, 31, 15, 0, tzinfo=UTC))

    with patch.object(export, "EXPORTS_DIR", str(tmp_path)):
        path = export.generate_csv(sync_session, 1, date(2024, 3, 1), date(2024, 3, 31))

    with open(path) as f:
        rows = list(csv.DictReader(f))
    assert [r["date"] for r in rows] == ["2024-03-31"]


async def test_pdf_export_includes_last_day(owner_with_transaction_at, sync_session, tmp_path):
    await owner_with_transaction_at(datetime(2024, 3, 31, 15, 0, tzinfo=UTC))

    with (
        patch.object(export, "EXPORTS_DIR", str(tmp_path)),
        patch("reportlab.platypus.Table") as table,
        patch("reportlab.platypus.SimpleDocTemplate"),
    ):
        export.generate_pdf(sync_session, 1, date(2024, 3, 1), date(2024, 3, 31))

    table_rows = table.call_args.args[0]
    assert len(table_rows) == 2  # header + the 2024-03-31 transaction


async def test_weekly_summary_includes_today(owner_with_transaction_at, sync_session):
    await owner_with_transaction_at(datetime.combine(date.today(), time(12, 0), tzinfo=UTC))

    with (
        patch("app.workers.tasks._get_session", return_value=sync_session),
        patch("app.utils.email.send_email") as send_email,
    ):
        send_weekly_summaries.run()

    send_email.assert_called_once()
    body = send_email.call_args.args[2]
    assert "Transactions: 1" in body
