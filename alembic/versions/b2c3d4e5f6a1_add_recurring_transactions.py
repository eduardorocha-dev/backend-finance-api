"""add recurring_transactions table

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-04-10 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b2c3d4e5f6a1"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Reuse existing enum — do NOT re-create it
_transactiontype = postgresql.ENUM(
    "income", "expense", "transfer", name="transactiontype", create_type=False
)


def upgrade() -> None:
    # Create new enum for recurrence frequency
    op.execute(
        "CREATE TYPE recurringfrequency AS ENUM ('daily', 'weekly', 'monthly', 'yearly')"
    )
    op.create_table(
        "recurring_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("type", _transactiontype, nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column(
            "frequency",
            postgresql.ENUM(
                "daily", "weekly", "monthly", "yearly",
                name="recurringfrequency",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("next_due_date", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_recurring_transactions_owner_id",
        "recurring_transactions",
        ["owner_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_recurring_transactions_owner_id", table_name="recurring_transactions")
    op.drop_table("recurring_transactions")
    op.execute("DROP TYPE recurringfrequency")
