"""add is_admin to users

Revision ID: 8901d018c6f9
Revises: f0adda1c9543
Create Date: 2026-09-24 18:47:49.282176

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "8901d018c6f9"
down_revision: Union[str, Sequence[str], None] = "f0adda1c9543"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default fills existing rows, so nobody becomes an admin by accident.
    op.add_column(
        "users",
        sa.Column("is_admin", sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("users", "is_admin")
