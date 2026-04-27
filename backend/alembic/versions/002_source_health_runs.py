"""Source health ledger tablosu

Revision ID: 002
Revises: 001
Create Date: 2026-04-24
"""
from alembic import op
import sqlalchemy as sa


revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "source_health_runs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("source_key", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("detail", sa.JSON(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        if_not_exists=True,
    )
    op.create_index(
        "ix_source_health_runs_source_key",
        "source_health_runs",
        ["source_key"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_source_health_runs_status",
        "source_health_runs",
        ["status"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_source_health_runs_recorded_at",
        "source_health_runs",
        ["recorded_at"],
        unique=False,
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_source_health_runs_recorded_at", table_name="source_health_runs")
    op.drop_index("ix_source_health_runs_status", table_name="source_health_runs")
    op.drop_index("ix_source_health_runs_source_key", table_name="source_health_runs")
    op.drop_table("source_health_runs")
