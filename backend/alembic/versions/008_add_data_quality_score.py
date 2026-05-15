"""add data_quality_score to stocks

Revision ID: 008
Revises: 007
Create Date: 2026-05-15
"""
from alembic import op
import sqlalchemy as sa

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("stocks")}
    if "data_quality_score" not in columns:
        op.add_column(
            "stocks",
            sa.Column("data_quality_score", sa.Float(), nullable=True),
        )


def downgrade() -> None:
    op.drop_column("stocks", "data_quality_score")
