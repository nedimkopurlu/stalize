"""add exit fields to portfolio_positions

Revision ID: 004
Revises: 003
Create Date: 2026-05-08
"""
from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("portfolio_positions", sa.Column("exit_price", sa.Float(), nullable=True))
    op.add_column("portfolio_positions", sa.Column("exit_date", sa.Date(), nullable=True))
    op.add_column("portfolio_positions", sa.Column("realized_pnl", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("portfolio_positions", "realized_pnl")
    op.drop_column("portfolio_positions", "exit_date")
    op.drop_column("portfolio_positions", "exit_price")
