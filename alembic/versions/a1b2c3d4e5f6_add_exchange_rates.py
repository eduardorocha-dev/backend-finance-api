"""add exchange_rates table

Revision ID: a1b2c3d4e5f6
Revises: 9523458320f8
Create Date: 2026-04-10 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "9523458320f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Reuse the existing enum — do NOT re-create it
_currencycode = postgresql.ENUM(
    "USD", "EUR", "BRL", "GBP", name="currencycode", create_type=False
)


def upgrade() -> None:
    op.create_table(
        "exchange_rates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("from_currency", _currencycode, nullable=False),
        sa.Column("to_currency", _currencycode, nullable=False),
        sa.Column("rate", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
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
        sa.CheckConstraint(
            "from_currency != to_currency", name="ck_exchange_rate_different_currencies"
        ),
        sa.CheckConstraint("rate > 0", name="ck_exchange_rate_positive"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "from_currency", "to_currency", "effective_date",
            name="uq_exchange_rate_pair_date",
        ),
    )


def downgrade() -> None:
    op.drop_table("exchange_rates")
