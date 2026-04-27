"""
Fundamental model — Temel analiz verileri
"""
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Fundamental(Base):
    """Fundamental analysis data for a stock (quarterly/annual)."""
    __tablename__ = "fundamentals"
    __table_args__ = (
        UniqueConstraint("stock_id", "period", "period_type", name="uq_stock_period"),
    )

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    period = Column(String(20), nullable=False)  # e.g. "2024-Q4", "2024-FY"
    period_type = Column(String(10), nullable=False)  # "quarterly" or "annual"

    # Valuation
    pe_ratio = Column(Float, nullable=True)         # F/K
    pb_ratio = Column(Float, nullable=True)         # PD/DD
    ev_ebitda = Column(Float, nullable=True)        # FD/FAVÖK
    eps = Column(Float, nullable=True)              # Hisse Başına Kar
    market_cap = Column(Float, nullable=True)       # Piyasa Değeri

    # Profitability
    roe = Column(Float, nullable=True)              # Özsermaye Karlılığı
    roa = Column(Float, nullable=True)              # Aktif Karlılığı
    net_margin = Column(Float, nullable=True)       # Net Kar Marjı
    gross_margin = Column(Float, nullable=True)     # Brüt Kar Marjı
    ebitda_margin = Column(Float, nullable=True)    # FAVÖK Marjı
    operating_margin = Column(Float, nullable=True) # Faaliyet Kar Marjı

    # Financial Health
    current_ratio = Column(Float, nullable=True)    # Cari Oran
    quick_ratio = Column(Float, nullable=True)      # Likidite Oranı
    debt_to_equity = Column(Float, nullable=True)   # Borç/Özsermaye
    interest_coverage = Column(Float, nullable=True) # Faiz Karşılama Oranı
    free_cash_flow = Column(Float, nullable=True)   # Serbest Nakit Akışı

    # Growth
    revenue = Column(Float, nullable=True)          # Gelir
    revenue_growth_yoy = Column(Float, nullable=True)  # Gelir Büyümesi YoY
    earnings_growth_yoy = Column(Float, nullable=True) # Kar Büyümesi YoY
    net_income = Column(Float, nullable=True)       # Net Kar

    # Dividends
    dividend_yield = Column(Float, nullable=True)   # Temettü Verimi
    dividend_payout_ratio = Column(Float, nullable=True) # Temettü Dağıtım Oranı

    # Quality Scores
    piotroski_score = Column(Integer, nullable=True)  # Piotroski F-Score (0-9)
    altman_z_score = Column(Float, nullable=True)     # Altman Z-Score

    # Overall fundamental score
    fundamental_score = Column(Float, nullable=True)  # 0-100

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    stock = relationship("Stock", back_populates="fundamentals")

    def __repr__(self):
        return f"<Fundamental(stock_id={self.stock_id}, period='{self.period}')>"
