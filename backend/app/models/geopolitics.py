"""
Geopolitics & Macro models — Jeopolitik olaylar ve makro ekonomik veriler
"""
from sqlalchemy import Column, Integer, Float, String, Text, DateTime, Date, JSON, Boolean
from sqlalchemy.sql import func
from app.core.database import Base


class GeopoliticalEvent(Base):
    """A geopolitical event that may affect BIST stocks."""
    __tablename__ = "geopolitical_events"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # war, sanctions, trade, energy, elections, etc.
    severity = Column(Integer, nullable=True)  # 1-10
    status = Column(String(20), default="active")  # active, resolved, escalating, de-escalating

    # Impact assessment
    turkey_impact = Column(String(20), nullable=True)  # direct, indirect, minimal
    duration_estimate = Column(String(20), nullable=True)  # short, medium, long
    affected_sectors = Column(JSON, nullable=True)  # List of affected sectors
    affected_stocks = Column(JSON, nullable=True)  # Dict of stock: impact direction

    # Source tracking
    source_urls = Column(JSON, nullable=True)  # List of source URLs
    first_detected = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<GeopoliticalEvent(title='{self.title[:50]}...', severity={self.severity})>"


class MacroIndicator(Base):
    """A macro-economic indicator reading."""
    __tablename__ = "macro_indicators"

    id = Column(Integer, primary_key=True, index=True)

    indicator_name = Column(String(100), nullable=False, index=True)  # e.g. "tcmb_policy_rate"
    category = Column(String(50), nullable=False)  # monetary, inflation, growth, trade, etc.
    country = Column(String(50), default="TR")
    date = Column(Date, nullable=False, index=True)
    value = Column(Float, nullable=False)
    previous_value = Column(Float, nullable=True)
    change = Column(Float, nullable=True)
    change_pct = Column(Float, nullable=True)
    unit = Column(String(20), nullable=True)  # %, bps, billion_usd, etc.
    source = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<MacroIndicator(name='{self.indicator_name}', date='{self.date}', value={self.value})>"


class EventImpactLog(Base):
    """Log of market event impacts for auditing."""
    __tablename__ = "event_impact_logs"

    id = Column(Integer, primary_key=True, index=True)

    trigger_type = Column(String(50), nullable=False)  # macro, geopolitical, commodity, currency, etc.
    trigger_description = Column(Text, nullable=False)
    chain_data = Column(JSON, nullable=False)  # Full chain traversal data
    affected_stocks = Column(JSON, nullable=True)  # Dict of stock: impact_score
    affected_sectors = Column(JSON, nullable=True)  # Dict of sector: impact_score
    confidence = Column(Float, nullable=True)
    was_accurate = Column(Boolean, nullable=True)  # For backtesting

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<EventImpactLog(trigger='{self.trigger_description[:50]}...')>"
