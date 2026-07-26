"""add description and images to invitation_templates, make preview_url nullable

Revision ID: f5g6h7i8j9k0
Revises: d3e4f5g6h7i8
Create Date: 2026-07-26 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "f5g6h7i8j9k0"
down_revision: Union[str, None] = "d3e4f5g6h7i8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "invitation_templates",
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.add_column(
        "invitation_templates",
        sa.Column("images", JSONB(), nullable=True),
    )
    op.alter_column(
        "invitation_templates",
        "preview_url",
        existing_type=sa.Text(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "invitation_templates",
        "preview_url",
        existing_type=sa.Text(),
        nullable=False,
    )
    op.drop_column("invitation_templates", "images")
    op.drop_column("invitation_templates", "description")
