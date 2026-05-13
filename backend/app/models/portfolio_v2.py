"""Model portföy ORM modelleri — MPRT-01"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.core.database import Base


class PortfolioPosition(Base):
    """
    Aktif veya kapatılmış portföy pozisyonu.
    Her pozisyon manuel olarak eklenir — sistem otomatik açmaz.
    """
    __tablename__ = "portfolio_positions"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)       # ör. "THYAO" (uzantısız)
    entry_price = Column(Float, nullable=False)                   # TRY giriş fiyatı
    quantity = Column(Float, nullable=False)                      # lot miktarı
    entry_date = Column(Date, nullable=False)                     # pozisyon açılış tarihi
    stop_loss = Column(Float, nullable=True)                      # ATR stop-loss seviyesi
    target_price = Column(Float, nullable=True)                   # hedef fiyat
    rationale = Column(Text, nullable=True)                       # pozisyon gerekçesi (Türkçe)
    is_active = Column(Boolean, default=True, nullable=False)     # False = kapatılmış
    exit_price = Column(Float, nullable=True)                     # TRY çıkış fiyatı (satış fiyatı)
    exit_date = Column(Date, nullable=True)                       # satış tarihi
    exit_reason = Column(String(50), nullable=True)               # çıkış nedeni: Stop Tetiklendi / Hedefe Ulaştı / Senaryo Bozuldu / Diğer: ...
    invalidation_condition = Column(Text, nullable=True)          # kararı bozan koşul (serbest metin)
    realized_pnl = Column(Float, nullable=True)                   # gerçekleşen kâr/zarar TRY
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PortfolioDailySnapshot(Base):
    """
    Her hafta içi 18:30'da alınan günlük portföy değer kaydı.
    Bir günde yalnızca bir snapshot — upsert ile güncellenir.
    """
    __tablename__ = "portfolio_daily_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True, index=True)  # bir günde tek snapshot
    total_value = Column(Float, nullable=False)                   # TRY toplam portföy değeri
    daily_pnl_pct = Column(Float, nullable=True)                  # günlük kazanç/kayıp (%)
    positions_json = Column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )                                                            # o günkü pozisyon detayları
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PortfolioChangeLog(Base):
    """
    Portföy değişiklik logu — pozisyon ekleme/çıkarma işlemleri.
    Sistem otomatik yazmaz, sadece API çağrısında oluşur.
    """
    __tablename__ = "portfolio_change_log"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    action = Column(String(10), nullable=False)                   # "ADD" veya "REMOVE"
    symbol = Column(String(20), nullable=False, index=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
