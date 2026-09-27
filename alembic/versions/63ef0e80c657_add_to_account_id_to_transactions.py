"""add to_account_id to transactions

Revision ID: 63ef0e80c657
Revises: 8901d018c6f9
Create Date: 2026-09-27 19:33:44.522986

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "63ef0e80c657"
down_revision: Union[str, Sequence[str], None] = "8901d018c6f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable: existing transfers have no recorded destination and keep working as
    # one-sided debits. New transfers must set it (enforced by the API).
    op.add_column("transactions", sa.Column("to_account_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_transactions_to_account_id_accounts",
        "transactions",
        "accounts",
        ["to_account_id"],
        ["id"],
    )
    op.create_index("ix_transactions_to_account_id", "transactions", ["to_account_id"])
    op.create_check_constraint(
        "ck_transactions_to_account_transfer",
        "transactions",
        "to_account_id IS NULL OR type = 'TRANSFER'",
    )
    op.create_check_constraint(
        "ck_transactions_to_account_differs",
        "transactions",
        "to_account_id IS NULL OR to_account_id <> account_id",
    )


def downgrade() -> None:
    op.drop_constraint("ck_transactions_to_account_differs", "transactions", type_="check")
    op.drop_constraint("ck_transactions_to_account_transfer", "transactions", type_="check")
    op.drop_index("ix_transactions_to_account_id", table_name="transactions")
    op.drop_constraint("fk_transactions_to_account_id_accounts", "transactions", type_="foreignkey")
    op.drop_column("transactions", "to_account_id")
