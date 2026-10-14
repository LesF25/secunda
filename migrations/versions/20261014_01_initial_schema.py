"""Create the initial payments and outbox schema.

Revision ID: 20261014_01
Revises:
Create Date: 2026-10-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '20261014_01'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'payments',
        sa.Column('idempotency_key', sa.Uuid(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('webhook_url', sa.String(length=2048), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column(
            'status',
            sa.String(length=20),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column(
            'meta_data',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('clock_timestamp()'),
            nullable=False,
        ),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'id',
            sa.Uuid(),
            server_default=sa.text('uuidv7()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_payments')),
        sa.UniqueConstraint(
            'idempotency_key',
            name=op.f('uq_payments_idempotency_key'),
        ),
    )

    op.create_table(
        'outbox',
        sa.Column('queue_name', sa.String(length=255), nullable=False),
        sa.Column(
            'payload',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column('lock_token', sa.Uuid(), nullable=True),
        sa.Column(
            'lock_expires_at',
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            'id',
            sa.Uuid(),
            server_default=sa.text('uuidv7()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_outbox')),
    )


def downgrade() -> None:
    op.drop_table('outbox')
    op.drop_table('payments')
