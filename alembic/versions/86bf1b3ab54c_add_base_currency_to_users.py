"""add base_currency to users

Revision ID: 86bf1b3ab54c
Revises: 63ef0e80c657
Create Date: 2026-09-29 20:41:14.640437

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "86bf1b3ab54c"
down_revision: Union[str, Sequence[str], None] = "63ef0e80c657"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Reuse the enum created for accounts.currency; don't create or drop it here.
_currencycode = postgresql.ENUM("USD", "EUR", "BRL", "GBP", name="currencycode", create_type=False)


def upgrade() -> None:
    # Existing users report in USD, which is what every amount was implicitly treated as.
    op.add_column(
        "users",
        sa.Column("base_currency", _currencycode, server_default="USD", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("users", "base_currency")
