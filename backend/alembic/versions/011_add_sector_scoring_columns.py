"""add sector scoring columns to stocks table

Revision ID: 011
Revises: 010
Create Date: 2026-05-15
"""
from alembic import op
import sqlalchemy as sa

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_cols = [c["name"] for c in inspector.get_columns("stocks")]

    if "sector_category" not in existing_cols:
        op.add_column("stocks", sa.Column("sector_category", sa.String(20), nullable=True))
    if "sector_score" not in existing_cols:
        op.add_column("stocks", sa.Column("sector_score", sa.Float(), nullable=True))
    if "sector_scoring_method" not in existing_cols:
        op.add_column("stocks", sa.Column("sector_scoring_method", sa.String(50), nullable=True))
    if "nav_discount" not in existing_cols:
        op.add_column("stocks", sa.Column("nav_discount", sa.Float(), nullable=True))


def downgrade() -> None:
    for col in ("nav_discount", "sector_scoring_method", "sector_score", "sector_category"):
        try:
            op.drop_column("stocks", col)
        except Exception:
            pass
