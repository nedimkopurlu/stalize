"""add sector to signal snapshots

Revision ID: 006
Revises: 005
Create Date: 2026-05-09
"""
from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("signal_decision_snapshots")}
    if "sector" not in columns:
        op.add_column("signal_decision_snapshots", sa.Column("sector", sa.String(length=100), nullable=True))

    table = sa.Table(
        "signal_decision_snapshots",
        sa.MetaData(),
        sa.Column("sector", sa.String(length=100)),
    )
    sa.Index("ix_signal_decision_snapshots_sector", table.c.sector).create(bind=bind, checkfirst=True)


def downgrade() -> None:
    op.drop_index("ix_signal_decision_snapshots_sector", table_name="signal_decision_snapshots")
    op.drop_column("signal_decision_snapshots", "sector")
