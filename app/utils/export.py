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

# Directory where generated export files are saved locally before upload.
EXPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "exports")


def _ensure_exports_dir() -> None:
    os.makedirs(EXPORTS_DIR, exist_ok=True)


def _upload_to_s3(filepath: str, filename: str) -> str:
    """Upload a file to S3 and return its public URL.

    Falls back to the local path if AWS credentials are not configured.
    """
    from app.core.config import settings

    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_BUCKET_NAME:
        return filepath

    import boto3

    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    s3.upload_file(filepath, settings.AWS_BUCKET_NAME, filename)
    return f"https://{settings.AWS_BUCKET_NAME}.s3.amazonaws.com/{filename}"


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
        writer.writerow(
            [
                row.date.strftime("%Y-%m-%d"),
                row.type.value,
                str(row.amount),
                row.description or "",
                row.category_name,
                row.account_name,
            ]
        )

    _ensure_exports_dir()
    filename = f"export_{uuid.uuid4().hex}.csv"
    filepath = os.path.abspath(os.path.join(EXPORTS_DIR, filename))
    with open(filepath, "w", newline="") as f:
        f.write(buffer.getvalue())

    return _upload_to_s3(filepath, filename)


def generate_pdf(session: Session, owner_id: int, date_from: date, date_to: date) -> str:
    """Generate a PDF export of the owner's transactions in the given date range.

    Returns the absolute path to the generated file.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet

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

    _ensure_exports_dir()
    filename = f"export_{uuid.uuid4().hex}.pdf"
    filepath = os.path.abspath(os.path.join(EXPORTS_DIR, filename))

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(filepath, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm)

    elements = []
    elements.append(Paragraph(f"Transaction Report", styles["Title"]))
    elements.append(Paragraph(f"{date_from} — {date_to}", styles["Normal"]))
    elements.append(Spacer(1, 0.5 * cm))

    table_data = [["Date", "Type", "Amount", "Description", "Category", "Account"]]
    for row in rows:
        table_data.append([
            row.date.strftime("%Y-%m-%d"),
            row.type.value,
            f"${row.amount:,.2f}",
            row.description or "",
            row.category_name,
            row.account_name,
        ])

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))

    elements.append(table)
    doc.build(elements)
    return _upload_to_s3(filepath, filename)
