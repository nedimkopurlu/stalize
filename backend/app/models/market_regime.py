"""MarketRegime model — günlük BIST100 piyasa rejimi"""
from sqlalchemy import Column, Integer, String, Float, Date, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class MarketRegime(Base):
    """Günlük BIST100 piyasa rejimi kaydı (Boğa/Ayı/Yatay/Volatil)."""

    __tablename__ = "market_regime"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True, index=True)
    regime = Column(String(20), nullable=False)
    adx = Column(Float, nullable=True)
    ema200 = Column(Float, nullable=True)
    atr = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<MarketRegime(date='{self.date}', regime='{self.regime}')>"
