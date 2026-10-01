"""rename export_jobs file_url to file_location

Revision ID: 97b532194a0e
Revises: 86bf1b3ab54c
Create Date: 2026-10-01 16:35:18.363223

"""

from typing import Sequence, Union

from alembic import op

revision: str = "97b532194a0e"
down_revision: Union[str, Sequence[str], None] = "86bf1b3ab54c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The column holds where the file is stored (local path or S3 location), which is
    # internal; the API now exposes a download link instead. Existing values stay valid.
    op.alter_column("export_jobs", "file_url", new_column_name="file_location")


def downgrade() -> None:
    op.alter_column("export_jobs", "file_location", new_column_name="file_url")
