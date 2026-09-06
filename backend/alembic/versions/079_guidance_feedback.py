"""create guidance feedback and suppression table

Revision ID: 079
Revises: 078
Create Date: 2026-09-08
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "079"
down_revision: Union[str, None] = "078"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use postgresql.UUID where available, fallback to CHAR(36) or sa.UUID
    uuid_type = sa.UUID()
    op.create_table(
        "guidance_feedback",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("workspace_id", uuid_type, nullable=False),
        sa.Column("user_id", uuid_type, nullable=False),
        sa.Column("insight_id", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("snoozed_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_helpful", sa.Boolean(), nullable=True),
        sa.Column("action_taken", sa.String(100), nullable=True),
        sa.Column("feedback_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_guidance_feedback_workspace_id", "guidance_feedback", ["workspace_id"]
    )
    op.create_index(
        "ix_guidance_feedback_user_id", "guidance_feedback", ["user_id"]
    )
    op.create_index(
        "ix_guidance_feedback_insight_id", "guidance_feedback", ["insight_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_guidance_feedback_insight_id", table_name="guidance_feedback")
    op.drop_index("ix_guidance_feedback_user_id", table_name="guidance_feedback")
    op.drop_index("ix_guidance_feedback_workspace_id", table_name="guidance_feedback")
    op.drop_table("guidance_feedback")
