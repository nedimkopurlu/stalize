"""TEFAS fon evreni snapshot ORM modeli."""

from sqlalchemy import Column, Date, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from app.core.database import Base


class TefasFundSnapshot(Base):
    """TEFAS fon evreninden alınan günlük fon snapshot kaydı."""

    __tablename__ = "tefas_fund_snapshots"
    __table_args__ = (
        UniqueConstraint("snapshot_date", "fund_code", name="uq_tefas_fund_snapshot_date_code"),
    )

    id = Column(Integer, primary_key=True, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    fund_code = Column(String(20), nullable=False, index=True)
    fund_name = Column(String(500), nullable=False)
    fund_type = Column(String(20), nullable=False, index=True)
    fund_type_label = Column(String(100), nullable=False)
    umbrella_type = Column(String(200), nullable=True)
    one_month_return_pct = Column(Float, nullable=True)
    three_month_return_pct = Column(Float, nullable=True)
    six_month_return_pct = Column(Float, nullable=True)
    year_to_date_return_pct = Column(Float, nullable=True)
    one_year_return_pct = Column(Float, nullable=True)
    three_year_return_pct = Column(Float, nullable=True)
    five_year_return_pct = Column(Float, nullable=True)
    detail_url = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
