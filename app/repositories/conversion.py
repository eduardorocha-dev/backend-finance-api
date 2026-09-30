"""SQL expressions that convert transaction amounts into a user's base currency.

Used inside queries that already join Transaction to Account. The rate for each
transaction is the most recent one effective on or before the transaction's date,
from the account's currency to the base currency. If only the opposite direction
was entered (e.g. USD→EUR when EUR→USD is needed), its inverse is used.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import ColumnElement, Select, case, func, literal, select

from app.models.account import Account, CurrencyCode
from app.models.exchange_rate import ExchangeRate
from app.models.transaction import Transaction, TransactionType


def rate_to(base: CurrencyCode) -> ColumnElement[Decimal]:
    """Rate from the transaction's account currency to `base`; NULL if none is known yet."""
    day = func.date(Transaction.date)
    direct = (
        select(ExchangeRate.rate)
        .where(
            ExchangeRate.from_currency == Account.currency,
            ExchangeRate.to_currency == base,
            ExchangeRate.effective_date <= day,
        )
        .order_by(ExchangeRate.effective_date.desc())
        .limit(1)
        .scalar_subquery()
    )
    inverse = (
        select(1 / ExchangeRate.rate)
        .where(
            ExchangeRate.from_currency == base,
            ExchangeRate.to_currency == Account.currency,
            ExchangeRate.effective_date <= day,
        )
        .order_by(ExchangeRate.effective_date.desc())
        .limit(1)
        .scalar_subquery()
    )
    return case(
        (Account.currency == base, literal(Decimal("1"))),
        else_=func.coalesce(direct, inverse),
    )


def converted_amount(base: CurrencyCode) -> ColumnElement[Decimal]:
    """The transaction's amount in `base`, rounded to cents (NULL if no rate is known)."""
    return func.round(Transaction.amount * rate_to(base), 2)


def first_missing_rate(owner_id: int, base: CurrencyCode, date_from: date, date_to: date) -> Select:
    """(currency, earliest date) of the first income/expense in the range with no usable rate.

    Returns no row when every transaction in the range can be converted.
    """
    day = func.date(Transaction.date)
    return (
        select(Account.currency, func.min(day).label("first_date"))
        .join(Account, Transaction.account_id == Account.id)
        .where(
            Account.owner_id == owner_id,
            Transaction.is_deleted == False,  # noqa: E712
            Transaction.type.in_([TransactionType.INCOME, TransactionType.EXPENSE]),
            day >= date_from,
            day <= date_to,
            rate_to(base).is_(None),
        )
        .group_by(Account.currency)
        .order_by(func.min(day))
        .limit(1)
    )
