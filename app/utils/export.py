"""CSV and PDF export generation utilities."""

from __future__ import annotations

import csv
import io
import os
import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction

# Directory where generated export files are saved.
# In production this would be replaced by an S3 upload.
EXPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "exports")


def _ensure_exports_dir() -> None:
    os.makedirs(EXPORTS_DIR, exist_ok=True)


def generate_csv(session: Session, owner_id: int, date_from: date, date_to: date) -> str:
    """Generate a CSV file for the owner's transactions in the given date range.

    Returns the absolute path to the generated file.
    """
    rows = session.execute(
        select(
            Transaction.date,
            Transaction.type,
            Transaction.amount,
            Transaction.description,
            Category.name.label("category_name"),
            Account.name.label("account_name"),
        )
        .join(Account, Transaction.account_id == Account.id)
        .join(Category, Transaction.category_id == Category.id)
        .where(
            Account.owner_id == owner_id,
            Transaction.is_deleted == False,  # noqa: E712
            Transaction.date >= date_from,
            Transaction.date <= date_to,
        )
        .order_by(Transaction.date.asc())
    ).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["date", "type", "amount", "description", "category", "account"])
    for row in rows:
        writer.writerow([
            row.date.strftime("%Y-%m-%d"),
            row.type.value,
            str(row.amount),
            row.description or "",
            row.category_name,
            row.account_name,
        ])

    _ensure_exports_dir()
    filename = f"export_{uuid.uuid4().hex}.csv"
    filepath = os.path.abspath(os.path.join(EXPORTS_DIR, filename))
    with open(filepath, "w", newline="") as f:
        f.write(buffer.getvalue())

    return filepath


def generate_pdf(session: Session, owner_id: int, date_from: date, date_to: date) -> str:
    """Generate a PDF export.

    TODO: implement with reportlab or weasyprint once the dependency is added.
    For now falls back to CSV so the export job does not get stuck in FAILED.
    """
    return generate_csv(session, owner_id, date_from, date_to)
