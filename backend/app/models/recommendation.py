"""Recommendation model — tavsiye kayıtları."""
from sqlalchemy import Column, Integer, Float, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Recommendation(Base):
    """A stock recommendation record with detailed reasoning."""
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)

    # Recommendation
    recommendation = Column(String(20), nullable=False)  # GÜÇLÜ AL, AL, TUT, SAT, GÜÇLÜ SAT
    overall_score = Column(Float, nullable=False)  # 0-100
    confidence = Column(Float, nullable=True)  # 0-100
    risk_level = Column(String(20), nullable=True)  # Düşük, Orta, Yüksek
    time_horizon = Column(String(20), nullable=True)  # Kısa, Orta, Uzun

    # Component scores
    technical_score = Column(Float, nullable=True)
    fundamental_score = Column(Float, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    macro_score = Column(Float, nullable=True)

    # Price targets
    current_price = Column(Float, nullable=True)
    target_price_low = Column(Float, nullable=True)
    target_price_mid = Column(Float, nullable=True)
    target_price_high = Column(Float, nullable=True)
    upside_potential = Column(Float, nullable=True)  # %

    # Detailed reasoning
    reasoning = Column(Text, nullable=True)  # Full text explanation
    key_factors = Column(JSON, nullable=True)  # List of key factors
    risk_factors = Column(JSON, nullable=True)  # List of risk factors

    # Technical signals
    technical_signals = Column(JSON, nullable=True)  # e.g. {"rsi": "oversold", "macd": "bullish_cross"}

    # Backtesting (after recommendation is old enough)
    actual_return_1w = Column(Float, nullable=True)  # Actual return after 1 week
    actual_return_1m = Column(Float, nullable=True)  # Actual return after 1 month
    actual_return_3m = Column(Float, nullable=True)  # Actual return after 3 months
    was_correct = Column(String(10), nullable=True)  # yes, no, partial

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    stock = relationship("Stock", back_populates="recommendations")

    def __repr__(self):
        return f"<Recommendation(stock_id={self.stock_id}, rec='{self.recommendation}', score={self.overall_score})>"
