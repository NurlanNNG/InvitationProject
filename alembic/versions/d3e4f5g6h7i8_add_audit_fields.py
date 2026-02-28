"""add audit fields (created_by_id, updated_by_id) to relevant tables

Revision ID: d3e4f5g6h7i8
Revises: c2d3e4f5g6h7
Create Date: 2026-03-01 02:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'd3e4f5g6h7i8'
down_revision: Union[str, None] = 'c2d3e4f5g6h7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── event_categories ─────────────────────────────────────────────────────
    op.add_column('event_categories',
        sa.Column('created_by_id', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))
    op.add_column('event_categories',
        sa.Column('updated_by_id', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))

    # ── invitation_templates ──────────────────────────────────────────────────
    op.add_column('invitation_templates',
        sa.Column('created_by_id', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))
    op.add_column('invitation_templates',
        sa.Column('updated_by_id', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))

    # ── payment_plans ─────────────────────────────────────────────────────────
    op.add_column('payment_plans',
        sa.Column('created_by_id', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))
    op.add_column('payment_plans',
        sa.Column('updated_by_id', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))

    # ── invitations ───────────────────────────────────────────────────────────
    op.add_column('invitations',
        sa.Column('updated_by_id', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))


def downgrade() -> None:
    op.drop_column('invitations', 'updated_by_id')
    op.drop_column('payment_plans', 'updated_by_id')
    op.drop_column('payment_plans', 'created_by_id')
    op.drop_column('invitation_templates', 'updated_by_id')
    op.drop_column('invitation_templates', 'created_by_id')
    op.drop_column('event_categories', 'updated_by_id')
    op.drop_column('event_categories', 'created_by_id')
