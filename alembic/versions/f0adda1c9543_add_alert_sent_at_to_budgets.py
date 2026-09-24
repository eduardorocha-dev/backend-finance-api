"""add alert_sent_at to budgets

Revision ID: f0adda1c9543
Revises: b2c3d4e5f6a1
Create Date: 2026-09-24 18:06:27.397510

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f0adda1c9543"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "budgets",
        sa.Column("alert_sent_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("budgets", "alert_sent_at")
