from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest

from app.models.portfolio_v2 import PortfolioDailySnapshot, PortfolioPosition
from app.services import portfolio_snapshot


class _FakeScalarResult:
    def __init__(self, payload):
        self._payload = payload

    def all(self):
        return self._payload


class _FakeResult:
    def __init__(self, payload):
        self._payload = payload

    def scalars(self):
        return _FakeScalarResult(self._payload)

    def scalar_one_or_none(self):
        return self._payload


class _FakeSession:
    def __init__(self, positions, existing_snapshot=None):
        self.positions = positions
        self.existing_snapshot = existing_snapshot
        self.added = []
        self.commit_count = 0

    async def execute(self, statement):
        entity = statement.column_descriptions[0]["entity"]
        if entity is PortfolioPosition:
            return _FakeResult(self.positions)
        if entity is PortfolioDailySnapshot:
            return _FakeResult(self.existing_snapshot)
        raise AssertionError(f"Unexpected entity in test session: {entity}")

    def add(self, obj):
        self.added.append(obj)
        if isinstance(obj, PortfolioDailySnapshot):
            self.existing_snapshot = obj

    async def commit(self):
        self.commit_count += 1


class _FakeSessionFactory:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def __call__(self):
        return self


@pytest.mark.asyncio
async def test_take_daily_snapshot_updates_existing_snapshot(monkeypatch):
    position = SimpleNamespace(
        symbol="THYAO",
        quantity=10,
        entry_price=100.0,
        stop_loss=90.0,
        target_price=130.0,
    )
    existing_snapshot = PortfolioDailySnapshot(
        date=date.today(),
        total_value=1000.0,
        daily_pnl_pct=0.0,
        positions_json=[{"symbol": "THYAO", "current_price": 100.0}],
        created_at=datetime.now(timezone.utc),
    )
    session = _FakeSession([position], existing_snapshot=existing_snapshot)
    success_calls = []
    failure_calls = []

    async def fake_fetch_price(_symbol):
        return 125.0

    monkeypatch.setattr(portfolio_snapshot, "AsyncSessionLocal", _FakeSessionFactory(session))
    monkeypatch.setattr(portfolio_snapshot, "_fetch_close_price", fake_fetch_price)
    monkeypatch.setattr(portfolio_snapshot, "record_source_success", lambda source, detail=None: success_calls.append((source, detail)))
    monkeypatch.setattr(portfolio_snapshot, "record_source_failure", lambda source, error, detail=None: failure_calls.append((source, error, detail)))

    await portfolio_snapshot.take_daily_snapshot()

    assert failure_calls == []
    assert session.added == []
    assert session.commit_count == 1
    assert existing_snapshot.total_value == 1250.0
    assert existing_snapshot.daily_pnl_pct == 25.0
    assert existing_snapshot.positions_json[0]["current_price"] == 125.0
    assert success_calls == [
        (
            "portfolio_snapshot",
            {
                "active_positions": 1,
                "priced_positions": 1,
                "skipped_symbols": [],
                "total_value": 1250.0,
                "daily_pnl_pct": 25.0,
            },
        )
    ]


@pytest.mark.asyncio
async def test_take_daily_snapshot_records_failure_when_no_prices(monkeypatch):
    position = SimpleNamespace(
        symbol="ASELS",
        quantity=5,
        entry_price=80.0,
        stop_loss=70.0,
        target_price=95.0,
    )
    session = _FakeSession([position])
    success_calls = []
    failure_calls = []

    async def fake_fetch_price(_symbol):
        return None

    monkeypatch.setattr(portfolio_snapshot, "AsyncSessionLocal", _FakeSessionFactory(session))
    monkeypatch.setattr(portfolio_snapshot, "_fetch_close_price", fake_fetch_price)
    monkeypatch.setattr(portfolio_snapshot, "record_source_success", lambda source, detail=None: success_calls.append((source, detail)))
    monkeypatch.setattr(portfolio_snapshot, "record_source_failure", lambda source, error, detail=None: failure_calls.append((source, error, detail)))

    await portfolio_snapshot.take_daily_snapshot()

    assert success_calls == []
    assert session.added == []
    assert session.commit_count == 0
    assert failure_calls == [
        (
            "portfolio_snapshot",
            "No close prices fetched for active portfolio positions",
            {
                "active_positions": 1,
                "priced_positions": 0,
                "skipped_symbols": ["ASELS"],
            },
        )
    ]
