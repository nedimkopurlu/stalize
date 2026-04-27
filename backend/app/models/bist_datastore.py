"""Borsa Istanbul Veri Store file snapshot ORM models."""

from sqlalchemy import BigInteger, Column, Date, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from app.core.database import Base


class BistDatastoreFileSnapshot(Base):
    """Kalici Veri Store dosya metadata snapshot kaydi."""

    __tablename__ = "bist_datastore_file_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "snapshot_date",
            "category_code",
            "product_type_id",
            "file_id",
            name="uq_bist_datastore_snapshot_file",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    category_code = Column(String(20), nullable=False, index=True)
    market = Column(String(120), nullable=True)
    market_key = Column(String(120), nullable=True, index=True)
    dataset_code = Column(String(120), nullable=True)
    dataset_title = Column(String(500), nullable=False)
    product_type_id = Column(String(50), nullable=False, index=True)
    file_id = Column(String(50), nullable=False, index=True)
    file_name = Column(String(500), nullable=False)
    file_date = Column(Date, nullable=True)
    create_date = Column(Date, nullable=True)
    file_size = Column(BigInteger, nullable=True)
    access_type = Column(String(20), nullable=True)
    update_frequency = Column(String(50), nullable=True)
    download_endpoint = Column(String(1000), nullable=True)
    catalog_url = Column(String(1000), nullable=True)
    datastore_url = Column(String(500), nullable=True)
    source = Column(String(120), nullable=False, default="Borsa İstanbul Veri Store")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
