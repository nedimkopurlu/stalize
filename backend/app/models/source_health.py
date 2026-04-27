"""Source health ledger ORM modeli."""

from sqlalchemy import Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class SourceHealthRun(Base):
    """Her kaynak denemesinin kalıcı sağlık kaydı."""

    __tablename__ = "source_health_runs"

    id = Column(Integer, primary_key=True, index=True)
    source_key = Column(String(100), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)
    error = Column(Text, nullable=True)
    detail = Column(JSON, nullable=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

