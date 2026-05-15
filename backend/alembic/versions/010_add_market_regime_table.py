"""create market_regime table

Revision ID: 010
Revises: 009
Create Date: 2026-05-15
"""
from alembic import op
import sqlalchemy as sa

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "market_regime" not in inspector.get_table_names():
        op.create_table(
            "market_regime",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("date", sa.Date(), nullable=False, unique=True),
            sa.Column("regime", sa.String(20), nullable=False),
            sa.Column("adx", sa.Float(), nullable=True),
            sa.Column("ema200", sa.Float(), nullable=True),
            sa.Column("atr", sa.Float(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
            ),
        )


def downgrade() -> None:
    op.drop_table("market_regime")
