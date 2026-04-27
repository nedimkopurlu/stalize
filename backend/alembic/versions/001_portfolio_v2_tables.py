"""Portfolio v2 tabloları — MPRT-01

Revision ID: 001
Revises:
Create Date: 2026-04-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tablolar daha önce Base.metadata.create_all ile oluşturulmuş olabilir.
    # checkfirst=True ile zaten varsa atla — idempotent migration.
    op.create_table(
        'portfolio_positions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('symbol', sa.String(20), nullable=False, index=True),
        sa.Column('entry_price', sa.Float(), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('entry_date', sa.Date(), nullable=False),
        sa.Column('stop_loss', sa.Float(), nullable=True),
        sa.Column('target_price', sa.Float(), nullable=True),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        if_not_exists=True,
    )
    op.create_table(
        'portfolio_daily_snapshots',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('date', sa.Date(), nullable=False, unique=True, index=True),
        sa.Column('total_value', sa.Float(), nullable=False),
        sa.Column('daily_pnl_pct', sa.Float(), nullable=True),
        sa.Column('positions_json', sa.JSON().with_variant(JSONB(), 'postgresql'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        if_not_exists=True,
    )
    op.create_table(
        'portfolio_change_log',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('date', sa.Date(), nullable=False, index=True),
        sa.Column('action', sa.String(10), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False, index=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        if_not_exists=True,
    )



def downgrade() -> None:
    op.drop_table('portfolio_change_log')
    op.drop_table('portfolio_daily_snapshots')
    op.drop_table('portfolio_positions')
