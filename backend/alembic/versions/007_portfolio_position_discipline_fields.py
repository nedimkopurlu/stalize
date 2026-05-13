"""add exit_reason and invalidation_condition to portfolio_positions

Revision ID: 007
Revises: 006
Create Date: 2026-05-14
"""
from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("portfolio_positions")}
    if "exit_reason" not in columns:
        op.add_column(
            "portfolio_positions",
            sa.Column("exit_reason", sa.String(50), nullable=True),
        )
    if "invalidation_condition" not in columns:
        op.add_column(
            "portfolio_positions",
            sa.Column("invalidation_condition", sa.Text(), nullable=True),
        )


def downgrade() -> None:
    op.drop_column("portfolio_positions", "invalidation_condition")
    op.drop_column("portfolio_positions", "exit_reason")
