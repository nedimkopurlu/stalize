"""Signal decision snapshots and measured outcomes."""
from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class SignalDecisionSnapshot(Base):
    """A persisted investment decision so future outcomes can be measured."""

    __tablename__ = "signal_decision_snapshots"
    __table_args__ = (
        UniqueConstraint("stock_id", "decision_date", name="uq_signal_stock_decision_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    sector = Column(String(100), nullable=True, index=True)
    decision_date = Column(Date, nullable=False, index=True)

    action = Column(String(24), nullable=False, index=True)
    action_label = Column(String(40), nullable=False)
    confidence = Column(Integer, nullable=False)
    risk_level = Column(String(16), nullable=False, index=True)
    time_horizon = Column(String(32), nullable=False)

    current_price = Column(Float, nullable=False)
    entry_low = Column(Float, nullable=True)
    entry_high = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    target_price = Column(Float, nullable=True)
    risk_reward = Column(Float, nullable=True)
    suggested_shares = Column(Integer, nullable=True)
    estimated_exposure = Column(Float, nullable=True)
    estimated_exposure_pct = Column(Float, nullable=True)

    overall_score = Column(Float, nullable=True)
    technical_score = Column(Float, nullable=True)
    fundamental_score = Column(Float, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    recommendation = Column(String(20), nullable=True)
    trend = Column(String(24), nullable=True)
    drawdown_pct = Column(Float, nullable=True)
    annualized_volatility_pct = Column(Float, nullable=True)

    benchmark_symbol = Column(String(30), nullable=True)
    benchmark_close = Column(Float, nullable=True)

    thesis_json = Column(JSON, nullable=True)
    invalidation = Column(Text, nullable=True)
    watch_items_json = Column(JSON, nullable=True)

    actual_close_1w = Column(Float, nullable=True)
    actual_return_1w_pct = Column(Float, nullable=True)
    benchmark_return_1w_pct = Column(Float, nullable=True)
    excess_return_1w_pct = Column(Float, nullable=True)
    outcome_1w = Column(String(16), nullable=True, index=True)

    actual_close_1m = Column(Float, nullable=True)
    actual_return_1m_pct = Column(Float, nullable=True)
    benchmark_return_1m_pct = Column(Float, nullable=True)
    excess_return_1m_pct = Column(Float, nullable=True)
    outcome_1m = Column(String(16), nullable=True, index=True)

    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    evaluated_at = Column(DateTime(timezone=True), nullable=True)

    stock = relationship("Stock")

    def __repr__(self) -> str:
        return f"<SignalDecisionSnapshot(symbol='{self.symbol}', action='{self.action}', date='{self.decision_date}')>"
