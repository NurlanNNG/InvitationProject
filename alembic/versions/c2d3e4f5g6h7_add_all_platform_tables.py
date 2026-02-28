"""add all platform tables: categories, templates, invitations, media, rsvp, payments

Revision ID: c2d3e4f5g6h7
Revises: b1c2d3e4f5g6
Create Date: 2026-03-01 01:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'c2d3e4f5g6h7'
down_revision: Union[str, None] = 'b1c2d3e4f5g6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ── Create all enum types up-front ────────────────────────────────────────────
_invitation_status = postgresql.ENUM(
    'draft', 'published', 'expired', 'archived',
    name='invitationstatus', create_type=False,
)
_media_type = postgresql.ENUM(
    'photo', 'cover', 'background',
    name='mediatype', create_type=False,
)
_display_style = postgresql.ENUM(
    'circle', 'square', 'rectangle',
    name='displaystyle', create_type=False,
)
_question_type = postgresql.ENUM(
    'boolean', 'number', 'text', 'select',
    name='questiontype', create_type=False,
)
_payment_status = postgresql.ENUM(
    'pending', 'success', 'failed', 'refunded',
    name='paymentstatus', create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()

    # Create enum types manually with IF NOT EXISTS semantics
    for enum_type in [_invitation_status, _media_type, _display_style, _question_type, _payment_status]:
        bind.execute(sa.text(
            f"DO $$ BEGIN "
            f"  CREATE TYPE {enum_type.name} AS ENUM ({', '.join(repr(v) for v in enum_type.enums)}); "
            f"EXCEPTION WHEN duplicate_object THEN null; "
            f"END $$;"
        ))

    # ── event_categories ──────────────────────────────────────────────────────
    op.create_table(
        'event_categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('slug', sa.String(length=50), nullable=False),
        sa.Column('name_kk', sa.String(length=100), nullable=False),
        sa.Column('name_ru', sa.String(length=100), nullable=False),
        sa.Column('name_en', sa.String(length=100), nullable=True),
        sa.Column('icon_url', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_event_categories_slug', 'event_categories', ['slug'], unique=True)

    # ── invitation_templates ──────────────────────────────────────────────────
    op.create_table(
        'invitation_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('name_kk', sa.String(length=150), nullable=False),
        sa.Column('name_ru', sa.String(length=150), nullable=False),
        sa.Column('preview_url', sa.Text(), nullable=False),
        sa.Column('thumbnail_url', sa.Text(), nullable=True),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('is_premium', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['event_categories.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── invitations ───────────────────────────────────────────────────────────
    op.create_table(
        'invitations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('status', _invitation_status, nullable=False, server_default='draft'),
        sa.Column('is_paid', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('editable_until', sa.DateTime(timezone=True), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['event_categories.id']),
        sa.ForeignKeyConstraint(['template_id'], ['invitation_templates.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_invitations_slug', 'invitations', ['slug'], unique=True)
    op.create_index('ix_invitations_user_id', 'invitations', ['user_id'], unique=False)

    # ── invitation_details ────────────────────────────────────────────────────
    op.create_table(
        'invitation_details',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invitation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organizer_name', sa.String(length=255), nullable=False),
        sa.Column('honoree_name', sa.String(length=255), nullable=True),
        sa.Column('invitation_text', sa.Text(), nullable=True),
        sa.Column('event_description', sa.Text(), nullable=True),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('event_time', sa.String(length=10), nullable=True),
        sa.Column('event_end_time', sa.String(length=10), nullable=True),
        sa.Column('dress_code', sa.String(length=255), nullable=True),
        sa.Column('venue_name', sa.String(length=255), nullable=True),
        sa.Column('venue_address', sa.Text(), nullable=True),
        sa.Column('venue_lat', sa.Numeric(precision=10, scale=8), nullable=True),
        sa.Column('venue_lng', sa.Numeric(precision=11, scale=8), nullable=True),
        sa.Column('venue_map_url', sa.Text(), nullable=True),
        sa.Column('contact_phone', sa.String(length=20), nullable=True),
        sa.Column('contact_name', sa.String(length=255), nullable=True),
        sa.Column('additional_info', sa.Text(), nullable=True),
        sa.Column('custom_fields', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['invitation_id'], ['invitations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invitation_id'),
    )
    op.create_index('ix_invitation_details_invitation_id', 'invitation_details', ['invitation_id'], unique=True)

    # ── invitation_media ──────────────────────────────────────────────────────
    op.create_table(
        'invitation_media',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invitation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('media_type', _media_type, nullable=False, server_default='photo'),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('thumbnail_url', sa.Text(), nullable=True),
        sa.Column('caption', sa.String(length=255), nullable=True),
        sa.Column('display_style', _display_style, nullable=False, server_default='rectangle'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['invitation_id'], ['invitations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_invitation_media_invitation_id', 'invitation_media', ['invitation_id'], unique=False)

    # ── rsvp_questions ────────────────────────────────────────────────────────
    op.create_table(
        'rsvp_questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invitation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_text_kk', sa.Text(), nullable=False),
        sa.Column('question_text_ru', sa.Text(), nullable=False),
        sa.Column('question_type', _question_type, nullable=False, server_default='text'),
        sa.Column('options', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['invitation_id'], ['invitations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_rsvp_questions_invitation_id', 'rsvp_questions', ['invitation_id'], unique=False)

    # ── rsvp_responses ────────────────────────────────────────────────────────
    op.create_table(
        'rsvp_responses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invitation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('guest_name', sa.String(length=255), nullable=False),
        sa.Column('guest_phone', sa.String(length=20), nullable=True),
        sa.Column('will_attend', sa.Boolean(), nullable=False),
        sa.Column('guest_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('answers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('responded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['invitation_id'], ['invitations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_rsvp_responses_invitation_id', 'rsvp_responses', ['invitation_id'], unique=False)
    op.create_index('ix_rsvp_responses_guest_phone', 'rsvp_responses', ['guest_phone'], unique=False)

    # ── payment_plans ─────────────────────────────────────────────────────────
    op.create_table(
        'payment_plans',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name_kk', sa.String(length=100), nullable=False),
        sa.Column('name_ru', sa.String(length=100), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='KZT'),
        sa.Column('max_guests', sa.Integer(), nullable=True),
        sa.Column('max_photos', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('validity_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('features', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── payments ──────────────────────────────────────────────────────────────
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('invitation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('plan_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='KZT'),
        sa.Column('status', _payment_status, nullable=False, server_default='pending'),
        sa.Column('payment_method', sa.String(length=50), nullable=False, server_default='kaspi'),
        sa.Column('kaspi_phone', sa.String(length=20), nullable=True),
        sa.Column('confirmed_by', sa.Integer(), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['confirmed_by'], ['users.id']),
        sa.ForeignKeyConstraint(['invitation_id'], ['invitations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['plan_id'], ['payment_plans.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_payments_user_id', 'payments', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('payments')
    op.drop_table('payment_plans')
    op.drop_table('rsvp_responses')
    op.drop_table('rsvp_questions')
    op.drop_table('invitation_media')
    op.drop_table('invitation_details')
    op.drop_table('invitations')
    op.drop_table('invitation_templates')
    op.drop_table('event_categories')

    bind = op.get_bind()
    for enum_name in ['paymentstatus', 'questiontype', 'displaystyle', 'mediatype', 'invitationstatus']:
        bind.execute(sa.text(f'DROP TYPE IF EXISTS {enum_name}'))
