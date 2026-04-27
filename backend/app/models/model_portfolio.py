"""Haftalık otomatik model portföy ORM modelleri."""
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from app.core.database import Base


class ModelPortfolioWeek(Base):
    """Sistemin her hafta ürettiği model portföy kaydı."""

    __tablename__ = "model_portfolio_weeks"
    __table_args__ = (
        UniqueConstraint("week_start", name="uq_model_portfolio_week_start"),
    )

    id = Column(Integer, primary_key=True, index=True)
    week_start = Column(Date, nullable=False, index=True)
    week_end = Column(Date, nullable=False, index=True)
    strategy_version = Column(String(32), nullable=False, default="v1")
    status = Column(String(20), nullable=False, default="active")  # active, reviewed, archived
    benchmark_symbol = Column(String(20), nullable=False, default="XU100.IS")
    benchmark_entry = Column(Float, nullable=True)
    benchmark_last = Column(Float, nullable=True)
    portfolio_return_pct = Column(Float, nullable=True)
    benchmark_return_pct = Column(Float, nullable=True)
    active_return_spread = Column(Float, nullable=True)
    daily_return_pct = Column(Float, nullable=True)
    review_summary = Column(Text, nullable=True)
    review_notes = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    generation_notes = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    holdings = relationship("ModelPortfolioHolding", back_populates="week", cascade="all, delete-orphan")
    snapshots = relationship("ModelPortfolioDailySnapshot", back_populates="week", cascade="all, delete-orphan")


class ModelPortfolioHolding(Base):
    """Haftalık model portföy içindeki tekil hisse satırı."""

    __tablename__ = "model_portfolio_holdings"
    __table_args__ = (
        UniqueConstraint("week_id", "symbol", name="uq_model_portfolio_week_symbol"),
    )

    id = Column(Integer, primary_key=True, index=True)
    week_id = Column(Integer, ForeignKey("model_portfolio_weeks.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    name = Column(String(200), nullable=True)
    sector = Column(String(100), nullable=True)
    allocation_pct = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=True)
    current_price = Column(Float, nullable=True)
    weekly_return_pct = Column(Float, nullable=True)
    daily_change_pct = Column(Float, nullable=True)
    technical_score = Column(Float, nullable=True)
    fundamental_score = Column(Float, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=True)
    recommendation = Column(String(20), nullable=True)
    rank = Column(Integer, nullable=False, default=0)
    rationale = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    week = relationship("ModelPortfolioWeek", back_populates="holdings")


class ModelPortfolioDailySnapshot(Base):
    """Aktif model portföy için günlük izleme kaydı."""

    __tablename__ = "model_portfolio_daily_snapshots"
    __table_args__ = (
        UniqueConstraint("week_id", "date", name="uq_model_portfolio_snapshot_week_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    week_id = Column(Integer, ForeignKey("model_portfolio_weeks.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    total_return_pct = Column(Float, nullable=True)
    daily_return_pct = Column(Float, nullable=True)
    benchmark_return_pct = Column(Float, nullable=True)
    active_return_spread = Column(Float, nullable=True)
    positions_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    week = relationship("ModelPortfolioWeek", back_populates="snapshots")
