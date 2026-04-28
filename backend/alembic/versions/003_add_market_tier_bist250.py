"""Add market_tier and is_bist250 to stocks

Revision ID: 003
Revises: 002
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "stocks",
        sa.Column("is_bist250", sa.Boolean(), nullable=True, server_default="false"),
    )
    op.add_column(
        "stocks",
        sa.Column("market_tier", sa.String(length=20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("stocks", "market_tier")
    op.drop_column("stocks", "is_bist250")
