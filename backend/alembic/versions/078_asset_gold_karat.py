"""add karat purity to gold holdings

Revision ID: 078
Revises: 077
Create Date: 2026-09-03

Physical gold is priced from a 24K spot gram quote. Jewellery is often 22K
or 18K, so we store the karat on the holding and scale last_price by k/24.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "078"
down_revision: Union[str, None] = "077"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("assets", sa.Column("karat", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("assets", "karat")
