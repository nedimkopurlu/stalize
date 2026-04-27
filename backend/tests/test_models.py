"""Tests for FOND-05: UTC timezone-aware datetime columns."""
import pytest
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.dialects import postgresql, sqlite


def test_portfolio_v2_timezone():
    """
    Portfolio v2 timestamp columns must use DateTime(timezone=True).
    Checked via SQLAlchemy column inspection (not DB round-trip).
    """
    from app.models.portfolio_v2 import PortfolioPosition, PortfolioDailySnapshot, PortfolioChangeLog
    from sqlalchemy import DateTime

    checks = [
        (PortfolioPosition, "created_at"),
        (PortfolioPosition, "updated_at"),
        (PortfolioDailySnapshot, "created_at"),
        (PortfolioChangeLog, "created_at"),
    ]

    for model, col_name in checks:
        mapper = sa_inspect(model)
        col_type = mapper.columns[col_name].type
        assert isinstance(col_type, DateTime), f"{model.__name__}.{col_name} is not DateTime"
        assert col_type.timezone is True, f"{model.__name__}.{col_name}.timezone must be True"


def test_source_health_run_timezone():
    from app.models.source_health import SourceHealthRun
    from sqlalchemy import DateTime

    mapper = sa_inspect(SourceHealthRun)
    col_type = mapper.columns["recorded_at"].type

    assert isinstance(col_type, DateTime)
    assert col_type.timezone is True


def test_tefas_snapshot_timezone():
    from app.models.fund_snapshot import TefasFundSnapshot
    from sqlalchemy import DateTime

    mapper = sa_inspect(TefasFundSnapshot)
    col_type = mapper.columns["created_at"].type

    assert isinstance(col_type, DateTime)
    assert col_type.timezone is True


def test_bist_datastore_snapshot_timezone():
    from app.models.bist_datastore import BistDatastoreFileSnapshot
    from sqlalchemy import DateTime

    mapper = sa_inspect(BistDatastoreFileSnapshot)
    col_type = mapper.columns["created_at"].type

    assert isinstance(col_type, DateTime)
    assert col_type.timezone is True


def test_portfolio_snapshot_positions_json_is_portable():
    from sqlalchemy import JSON
    from sqlalchemy.dialects.postgresql import JSONB

    from app.models.portfolio_v2 import PortfolioDailySnapshot

    mapper = sa_inspect(PortfolioDailySnapshot)
    col_type = mapper.columns["positions_json"].type

    sqlite_impl = col_type.dialect_impl(sqlite.dialect())
    postgres_impl = col_type.dialect_impl(postgresql.dialect())

    assert isinstance(sqlite_impl, JSON)
    assert isinstance(postgres_impl, JSONB)
