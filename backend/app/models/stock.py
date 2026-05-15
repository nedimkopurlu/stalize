"""
Stock model — BIST hisse senedi bilgileri
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Stock(Base):
    """A BIST stock with its metadata and sector information."""
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)  # e.g. THYAO
    yahoo_symbol = Column(String(25), nullable=False)  # e.g. THYAO.IS
    name = Column(String(200), nullable=True)
    sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    market_cap = Column(Float, nullable=True)
    currency = Column(String(10), default="TRY")
    is_bist30 = Column(Boolean, default=False)
    is_bist100 = Column(Boolean, default=True)
    is_bist250 = Column(Boolean, default=False)
    market_tier = Column(String(20), nullable=True)  # yıldız / ana / gelişen
    is_active = Column(Boolean, default=True)

    # Current price data (cached)
    current_price = Column(Float, nullable=True)
    daily_change_pct = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)

    # Analysis scores (cached, updated periodically)
    technical_score = Column(Float, nullable=True)
    fundamental_score = Column(Float, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=True)
    recommendation = Column(String(20), nullable=True)  # GÜÇLÜ AL, AL, TUT, SAT, GÜÇLÜ SAT
    data_quality_score = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_data_update = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    prices = relationship("PriceHistory", back_populates="stock", cascade="all, delete-orphan")
    fundamentals = relationship("Fundamental", back_populates="stock", cascade="all, delete-orphan")
    news_items = relationship("NewsItem", back_populates="stock", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="stock", cascade="all, delete-orphan")
    def __repr__(self):
        return f"<Stock(symbol='{self.symbol}', name='{self.name}')>"
