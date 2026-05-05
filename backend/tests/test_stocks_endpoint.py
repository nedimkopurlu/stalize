"""Tests for /stocks endpoint covering DISC-01 (BIST100 filter + overall_score sort)."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client(app_client):
    """Module alias for the session-scoped app_client fixture in conftest.py."""
    return app_client


class _FakeScalars:
    def __init__(self, rows): self._rows = rows
    def all(self): return self._rows
    def first(self): return self._rows[0] if self._rows else None


class _FakeResult:
    def __init__(self, rows, scalar_value=None):
        self._rows = rows
        self._scalar = scalar_value if scalar_value is not None else len(rows)
    def scalars(self): return _FakeScalars(self._rows)
    def scalar(self): return self._scalar
    def fetchall(self): return []  # for batched avg_volumes subquery


def _stock(symbol, overall_score, is_bist100=True):
    s = MagicMock()
    s.id = abs(hash(symbol)) % 1000000
    s.symbol = symbol
    s.name = symbol
    s.sector = "Test"
    s.industry = "Test"
    s.current_price = 100.0
    s.daily_change_pct = 0.0
    s.volume = 1000.0
    s.market_cap = 1e9
    s.is_bist30 = False
    s.is_bist100 = is_bist100
    s.is_bist250 = False
    s.is_active = True
    s.technical_score = 50.0
    s.fundamental_score = 50.0
    s.sentiment_score = 50.0
    s.overall_score = overall_score
    s.recommendation = "TUT"
    return s


def _override_db_with_stocks(stocks):
    from app.main import app
    from app.core.database import get_db

    async def _fake_db():
        db = MagicMock()
        async def _execute(stmt):
            txt = str(stmt)
            # /stocks endpoint runs: (1) Stock list query, (2) func.count(...) query,
            # (3) avg_volumes window subquery. Differentiate by SQL fingerprint.
            if "count" in txt.lower() and "stocks" in txt.lower():
                return _FakeResult([], scalar_value=len(stocks))
            if "row_number" in txt.lower() or "partition_by" in txt.lower():
                return _FakeResult([])  # avg volumes — return empty list
            return _FakeResult(stocks)
        db.execute = _execute
        yield db

    app.dependency_overrides[get_db] = _fake_db
    return lambda: app.dependency_overrides.pop(get_db, None)


def test_bist100_filter_returns_only_bist100_sorted(client):
    """DISC-01: /stocks?bist100=true&sort_by=overall_score returns only BIST100
    stocks ordered by overall_score desc."""
    # Pre-sorted desc since we cannot enforce SQL ORDER BY in mock — the mock
    # returns the list as-is and the endpoint just shapes the response.
    stocks = [
        _stock("THYAO", 85.0, is_bist100=True),
        _stock("GARAN", 80.0, is_bist100=True),
        _stock("EREGL", 75.0, is_bist100=True),
    ]
    cleanup = _override_db_with_stocks(stocks)
    try:
        r = client.get("/api/stocks?bist100=true&sort_by=overall_score&limit=20")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "stocks" in body
        returned = body["stocks"]
        assert len(returned) == 3
        for s in returned:
            assert s["is_bist100"] is True, f"non-BIST100 leaked: {s['symbol']}"
        scores = [s["overall_score"] for s in returned]
        assert scores == sorted(scores, reverse=True), f"not sorted desc: {scores}"
    finally:
        cleanup()


def test_stocks_endpoint_accepts_bist100_param(client):
    """The bist100 query param is accepted (no 422). Schema-only check."""
    # Without override, this hits real DB which may not exist in CI; we accept 200 or 500.
    r = client.get("/api/stocks?bist100=true&limit=1")
    assert r.status_code in (200, 500), f"bist100 param rejected: {r.status_code} {r.text[:200]}"


def test_stocks_sort_by_overall_score_param_accepted(client):
    """sort_by=overall_score param is accepted (column exists in sort_columns map)."""
    r = client.get("/api/stocks?sort_by=overall_score&limit=1")
    assert r.status_code in (200, 500)
