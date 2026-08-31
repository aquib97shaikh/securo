"""store instance Google Drive backup connection

Revision ID: 077
Revises: 076
Create Date: 2026-08-31
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "077"
down_revision: Union[str, None] = "076"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "drive_backup_config",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("folder_id", sa.String(128), nullable=True),
        sa.Column("google_email", sa.String(320), nullable=True),
        sa.Column("schedule", sa.String(16), nullable=False, server_default="daily"),
        sa.Column("password_encrypted", sa.Text(), nullable=True),
        sa.Column("latest_file_ids", sa.JSON(), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_ok", sa.Boolean(), nullable=True),
        sa.Column("last_run_error", sa.String(500), nullable=True),
        sa.Column("last_scheduled_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("drive_backup_config")
