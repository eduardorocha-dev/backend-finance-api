"""Reports convert every account's amounts into the user's base currency.

Rates are looked up per transaction: the latest rate effective on or before the
transaction's date. A rate for the opposite direction is used inverted.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models.account import CurrencyCode
from app.models.exchange_rate import ExchangeRate
from app.workers.tasks import send_weekly_summaries

REPORTS = "/api/v1/reports"
MARCH = {"month": "2024-03-01"}


@pytest.fixture
async def headers(client: AsyncClient) -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "full_name": "Test User", "password": "secret123"},
    )
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "user@example.com", "password": "secret123"}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def add_rate(session: Session, from_: str, to: str, rate: str, effective: date) -> None:
    session.add(
        ExchangeRate(
            from_currency=CurrencyCode(from_),
            to_currency=CurrencyCode(to),
            rate=Decimal(rate),
            effective_date=effective,
        )
    )
    session.commit()


@pytest.fixture
async def books(client: AsyncClient, headers: dict) -> dict:
    """A USD account with 100 of income and a EUR account with two 50 EUR expenses."""

    async def post(path: str, **body) -> dict:
        resp = await client.post(f"/api/v1/{path}", json=body, headers=headers)
        assert resp.status_code == 201, resp.text
        return resp.json()

    usd = await post("accounts", name="Checking", type="checking", currency="USD")
    eur = await post("accounts", name="Euro card", type="credit", currency="EUR")
    food = await post("categories", name="Food")
    salary = await post("categories", name="Salary")

    async def tx(account: dict, category: dict, type_: str, amount: str, day: str) -> None:
        await post(
            "transactions",
            account_id=account["id"],
            category_id=category["id"],
            type=type_,
            amount=amount,
            date=f"2024-03-{day}T12:00:00Z",
        )

    with patch("app.workers.tasks.send_budget_alert.delay"):
        await tx(usd, salary, "income", "100.00", "02")
        await tx(eur, food, "expense", "50.00", "05")
        await tx(eur, food, "expense", "50.00", "20")
    return {"usd": usd, "eur": eur, "food": food}


@pytest.fixture
def march_rates(sync_session: Session) -> None:
    """EUR→USD is 1.10 from March 1st and 1.20 from March 15th."""
    add_rate(sync_session, "EUR", "USD", "1.100000", date(2024, 3, 1))
    add_rate(sync_session, "EUR", "USD", "1.200000", date(2024, 3, 15))


# ── Conversion ────────────────────────────────────────────────────────────────


async def test_monthly_converts_with_rate_on_each_transaction_date(
    client: AsyncClient, headers: dict, books: dict, march_rates
):
    resp = await client.get(f"{REPORTS}/monthly", params=MARCH, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["currency"] == "USD"
    assert Decimal(data["total_income"]) == Decimal("100.00")
    # 50 EUR × 1.10 on the 5th + 50 EUR × 1.20 on the 20th
    assert Decimal(data["total_expenses"]) == Decimal("115.00")
    assert Decimal(data["net"]) == Decimal("-15.00")


async def test_category_breakdown_is_converted(
    client: AsyncClient, headers: dict, books: dict, march_rates
):
    data = (await client.get(f"{REPORTS}/categories", params=MARCH, headers=headers)).json()
    assert data["currency"] == "USD"
    assert Decimal(data["total_expenses"]) == Decimal("115.00")
    assert [(b["category_name"], Decimal(b["total_amount"])) for b in data["breakdown"]] == [
        ("Food", Decimal("115.00"))
    ]


async def test_cashflow_is_converted(client: AsyncClient, headers: dict, books: dict, march_rates):
    params = {"date_from": "2024-03-01", "date_to": "2024-03-31"}
    data = (await client.get(f"{REPORTS}/cashflow", params=params, headers=headers)).json()
    assert data["currency"] == "USD"
    rows = [
        (e["period"], Decimal(e["expenses"]), Decimal(e["cumulative_net"])) for e in data["entries"]
    ]
    assert rows == [
        ("2024-03-02", Decimal("0"), Decimal("100.00")),
        ("2024-03-05", Decimal("55.00"), Decimal("45.00")),
        ("2024-03-20", Decimal("60.00"), Decimal("-15.00")),
    ]


async def test_uses_inverse_rate_when_only_opposite_direction_exists(
    client: AsyncClient, headers: dict, books: dict, sync_session: Session
):
    add_rate(sync_session, "USD", "EUR", "0.800000", date(2024, 3, 1))  # so EUR→USD = 1.25

    data = (await client.get(f"{REPORTS}/monthly", params=MARCH, headers=headers)).json()
    assert Decimal(data["total_expenses"]) == Decimal("125.00")


async def test_missing_rate_is_an_error_not_a_wrong_total(
    client: AsyncClient, headers: dict, books: dict
):
    resp = await client.get(f"{REPORTS}/monthly", params=MARCH, headers=headers)
    assert resp.status_code == 422
    assert "EUR" in resp.json()["detail"] and "USD" in resp.json()["detail"]
    assert "2024-03-05" in resp.json()["detail"]


async def test_rate_effective_after_the_transaction_is_not_used(
    client: AsyncClient, headers: dict, books: dict, sync_session: Session
):
    # Only a rate from March 10th exists; the March 5th expense has nothing to use.
    add_rate(sync_session, "EUR", "USD", "1.100000", date(2024, 3, 10))
    resp = await client.get(f"{REPORTS}/monthly", params=MARCH, headers=headers)
    assert resp.status_code == 422


# ── Base currency ─────────────────────────────────────────────────────────────


async def test_base_currency_defaults_to_usd_and_can_be_changed(
    client: AsyncClient, headers: dict, books: dict, march_rates
):
    me = "/api/v1/auth/me"
    assert (await client.get(me, headers=headers)).json()["base_currency"] == "USD"

    resp = await client.patch(me, json={"base_currency": "EUR"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["base_currency"] == "EUR"

    data = (await client.get(f"{REPORTS}/monthly", params=MARCH, headers=headers)).json()
    assert data["currency"] == "EUR"
    assert Decimal(data["total_expenses"]) == Decimal("100.00")  # EUR needs no conversion
    # 100 USD on March 2nd ÷ 1.10 (inverse of EUR→USD)
    assert Decimal(data["total_income"]) == Decimal("90.91")


async def test_register_with_base_currency(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "eu@example.com",
            "full_name": "EU User",
            "password": "secret123",
            "base_currency": "EUR",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["base_currency"] == "EUR"


# ── Weekly summary email ──────────────────────────────────────────────────────


async def test_weekly_summary_converts_and_names_the_currency(
    client: AsyncClient, headers: dict, books: dict, march_rates, sync_session: Session
):
    class FakeDate(date):
        @classmethod
        def today(cls) -> date:
            return date(2024, 3, 21)  # the week of March 14–21 holds the 60 USD expense

    with (
        patch("app.workers.tasks._get_session", return_value=sync_session),
        patch("app.workers.tasks.date", FakeDate),
        patch("app.utils.email.send_email") as send_email,
    ):
        send_weekly_summaries.run()

    body = send_email.call_args.args[2]
    assert "Expenses: 60.00 USD" in body
    assert "$" not in body


async def test_weekly_summary_skips_user_without_a_rate(
    client: AsyncClient, headers: dict, books: dict, sync_session: Session, caplog
):
    class FakeDate(date):
        @classmethod
        def today(cls) -> date:
            return date(2024, 3, 21)

    with (
        patch("app.workers.tasks._get_session", return_value=sync_session),
        patch("app.workers.tasks.date", FakeDate),
        patch("app.utils.email.send_email") as send_email,
    ):
        send_weekly_summaries.run()

    send_email.assert_not_called()  # no EUR→USD rate: no email with made-up totals
    assert "no EUR→USD rate" in caplog.text
