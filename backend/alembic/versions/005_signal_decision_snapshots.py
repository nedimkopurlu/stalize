"""add signal decision snapshots

Revision ID: 005
Revises: 004
Create Date: 2026-05-09
"""
from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_name = "signal_decision_snapshots"

    if not inspector.has_table(table_name):
        op.create_table(
            table_name,
            sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("stock_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("sector", sa.String(length=100), nullable=True),
        sa.Column("decision_date", sa.Date(), nullable=False),
            sa.Column("action", sa.String(length=24), nullable=False),
            sa.Column("action_label", sa.String(length=40), nullable=False),
            sa.Column("confidence", sa.Integer(), nullable=False),
            sa.Column("risk_level", sa.String(length=16), nullable=False),
            sa.Column("time_horizon", sa.String(length=32), nullable=False),
            sa.Column("current_price", sa.Float(), nullable=False),
            sa.Column("entry_low", sa.Float(), nullable=True),
            sa.Column("entry_high", sa.Float(), nullable=True),
            sa.Column("stop_loss", sa.Float(), nullable=True),
            sa.Column("target_price", sa.Float(), nullable=True),
            sa.Column("risk_reward", sa.Float(), nullable=True),
            sa.Column("suggested_shares", sa.Integer(), nullable=True),
            sa.Column("estimated_exposure", sa.Float(), nullable=True),
            sa.Column("estimated_exposure_pct", sa.Float(), nullable=True),
            sa.Column("overall_score", sa.Float(), nullable=True),
            sa.Column("technical_score", sa.Float(), nullable=True),
            sa.Column("fundamental_score", sa.Float(), nullable=True),
            sa.Column("sentiment_score", sa.Float(), nullable=True),
            sa.Column("recommendation", sa.String(length=20), nullable=True),
            sa.Column("trend", sa.String(length=24), nullable=True),
            sa.Column("drawdown_pct", sa.Float(), nullable=True),
            sa.Column("annualized_volatility_pct", sa.Float(), nullable=True),
            sa.Column("benchmark_symbol", sa.String(length=30), nullable=True),
            sa.Column("benchmark_close", sa.Float(), nullable=True),
            sa.Column("thesis_json", sa.JSON(), nullable=True),
            sa.Column("invalidation", sa.Text(), nullable=True),
            sa.Column("watch_items_json", sa.JSON(), nullable=True),
            sa.Column("actual_close_1w", sa.Float(), nullable=True),
            sa.Column("actual_return_1w_pct", sa.Float(), nullable=True),
            sa.Column("benchmark_return_1w_pct", sa.Float(), nullable=True),
            sa.Column("excess_return_1w_pct", sa.Float(), nullable=True),
            sa.Column("outcome_1w", sa.String(length=16), nullable=True),
            sa.Column("actual_close_1m", sa.Float(), nullable=True),
            sa.Column("actual_return_1m_pct", sa.Float(), nullable=True),
            sa.Column("benchmark_return_1m_pct", sa.Float(), nullable=True),
            sa.Column("excess_return_1m_pct", sa.Float(), nullable=True),
            sa.Column("outcome_1m", sa.String(length=16), nullable=True),
            sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("stock_id", "decision_date", name="uq_signal_stock_decision_date"),
        )

    metadata = sa.MetaData()
    table = sa.Table(
        table_name,
        metadata,
        sa.Column("id", sa.Integer()),
        sa.Column("stock_id", sa.Integer()),
        sa.Column("symbol", sa.String(length=20)),
        sa.Column("sector", sa.String(length=100)),
        sa.Column("decision_date", sa.Date()),
        sa.Column("action", sa.String(length=24)),
        sa.Column("risk_level", sa.String(length=16)),
        sa.Column("outcome_1w", sa.String(length=16)),
        sa.Column("outcome_1m", sa.String(length=16)),
    )
    for name, columns in [
        (op.f("ix_signal_decision_snapshots_id"), ["id"]),
        ("ix_signal_decision_snapshots_stock_id", ["stock_id"]),
        ("ix_signal_decision_snapshots_symbol", ["symbol"]),
        ("ix_signal_decision_snapshots_sector", ["sector"]),
        ("ix_signal_decision_snapshots_decision_date", ["decision_date"]),
        ("ix_signal_decision_snapshots_action", ["action"]),
        ("ix_signal_decision_snapshots_risk_level", ["risk_level"]),
        ("ix_signal_decision_snapshots_outcome_1w", ["outcome_1w"]),
        ("ix_signal_decision_snapshots_outcome_1m", ["outcome_1m"]),
    ]:
        sa.Index(name, *[getattr(table.c, col) for col in columns]).create(bind=bind, checkfirst=True)


def downgrade() -> None:
    op.drop_index("ix_signal_decision_snapshots_outcome_1m", table_name="signal_decision_snapshots")
    op.drop_index("ix_signal_decision_snapshots_outcome_1w", table_name="signal_decision_snapshots")
    op.drop_index("ix_signal_decision_snapshots_risk_level", table_name="signal_decision_snapshots")
    op.drop_index("ix_signal_decision_snapshots_action", table_name="signal_decision_snapshots")
    op.drop_index("ix_signal_decision_snapshots_decision_date", table_name="signal_decision_snapshots")
    op.drop_index("ix_signal_decision_snapshots_symbol", table_name="signal_decision_snapshots")
    op.drop_index("ix_signal_decision_snapshots_stock_id", table_name="signal_decision_snapshots")
    op.drop_index(op.f("ix_signal_decision_snapshots_id"), table_name="signal_decision_snapshots")
    op.drop_table("signal_decision_snapshots")
