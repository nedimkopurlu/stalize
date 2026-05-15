"""add liquidity scoring and kap_category columns

Revision ID: 009
Revises: 008
Create Date: 2026-05-15
"""
from alembic import op
import sqlalchemy as sa

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # stocks table columns
    stock_cols = {col["name"] for col in inspector.get_columns("stocks")}
    if "liquidity_score" not in stock_cols:
        op.add_column(
            "stocks",
            sa.Column("liquidity_score", sa.String(20), nullable=True),
        )
    if "amihud_ratio" not in stock_cols:
        op.add_column(
            "stocks",
            sa.Column("amihud_ratio", sa.Float(), nullable=True),
        )

    # news_items table columns
    news_cols = {col["name"] for col in inspector.get_columns("news_items")}
    if "kap_category" not in news_cols:
        op.add_column(
            "news_items",
            sa.Column("kap_category", sa.String(50), nullable=True),
        )


def downgrade() -> None:
    op.drop_column("news_items", "kap_category")
    op.drop_column("stocks", "amihud_ratio")
    op.drop_column("stocks", "liquidity_score")
