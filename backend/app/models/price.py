"""
Price History model — OHLCV fiyat geçmişi
"""
from sqlalchemy import Column, Integer, Float, String, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class PriceHistory(Base):
    """Daily OHLCV price data for a stock."""
    __tablename__ = "price_history"
    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_stock_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    open = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    close = Column(Float, nullable=False)
    adj_close = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)

    # Pre-calculated technical indicators (cached for performance)
    sma_20 = Column(Float, nullable=True)
    sma_50 = Column(Float, nullable=True)
    sma_200 = Column(Float, nullable=True)
    ema_12 = Column(Float, nullable=True)
    ema_26 = Column(Float, nullable=True)
    rsi_14 = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)
    macd_histogram = Column(Float, nullable=True)
    bb_upper = Column(Float, nullable=True)
    bb_middle = Column(Float, nullable=True)
    bb_lower = Column(Float, nullable=True)
    atr_14 = Column(Float, nullable=True)
    obv = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    stock = relationship("Stock", back_populates="prices")

    def __repr__(self):
        return f"<PriceHistory(stock_id={self.stock_id}, date='{self.date}', close={self.close})>"


class CommodityPrice(Base):
    """Daily price data for commodities, indices, currencies."""
    __tablename__ = "commodity_prices"
    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_commodity_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(30), nullable=False, index=True)  # e.g. BZ=F, GC=F
    name = Column(String(100), nullable=True)  # e.g. Brent Oil, Gold
    category = Column(String(50), nullable=True)  # commodity, index, currency, bond
    date = Column(Date, nullable=False, index=True)
    close = Column(Float, nullable=False)
    open = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)
    change_pct = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<CommodityPrice(symbol='{self.symbol}', date='{self.date}', close={self.close})>"
