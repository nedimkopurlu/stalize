"""Tests for /market/* endpoints (Phase 28). Plan 28-01 ships the scaffolding;
Plan 28-02 implements bist100/forex/gold; Plan 28-03 implements opportunities."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture(scope="module")
def client(app_client):
    """Module alias for the session-scoped app_client fixture in conftest.py."""
    return app_client


def _make_commodity_row(symbol: str, d: date, close: float, volume: float = 0.0):
    row = MagicMock()
    row.symbol = symbol
    row.date = d
    row.close = close
    row.volume = volume
    return row


class _FakeScalars:
    def __init__(self, rows): self._rows = rows
    def all(self): return self._rows
    def first(self): return self._rows[0] if self._rows else None
    def scalar_one_or_none(self): return self._rows[0] if self._rows else None


class _FakeResult:
    def __init__(self, rows): self._rows = rows
    def scalars(self): return _FakeScalars(self._rows)


def _override_db_with_rows_map(client, rows_by_symbol: dict):
    """Replace get_db with a stub that returns rows filtered by symbol from rows_by_symbol."""
    from app.main import app
    from app.core.database import get_db

    async def _fake_db():
        db = MagicMock()
        async def _execute(stmt):
            # crude: stringify the compiled SQL and look for any of the symbols
            txt = str(stmt.compile(compile_kwargs={"literal_binds": True}))
            for sym, rows in rows_by_symbol.items():
                if sym in txt:
                    return _FakeResult(rows)
            return _FakeResult([])
        db.execute = _execute
        yield db

    app.dependency_overrides[get_db] = _fake_db
    return lambda: app.dependency_overrides.pop(get_db, None)


def test_market_router_mounted(client):
    """Plan 28-01: market router must be mounted under /api."""
    r = client.get("/api/market/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("router") == "market"
    assert body.get("status") == "ok"


# ─── BIST100 TESTS ───


def test_bist100_endpoint_returns_value_and_change(client):
    today = date.today()
    rows = [
        _make_commodity_row("XU100.IS", today, close=10500.0, volume=0),       # newest first
        _make_commodity_row("XU100.IS", today - timedelta(days=1), close=10000.0, volume=0),
    ]
    cleanup = _override_db_with_rows_map(client, {"XU100.IS": rows})
    try:
        # Bypass cache: clear it first
        from app.api.market import _market_cache
        _market_cache.clear()
        r = client.get("/api/market/bist100")
        assert r.status_code == 200
        body = r.json()
        assert body["value"] == 10500.0
        assert body["daily_change_pct"] == 5.0  # (10500-10000)/10000*100
        assert body["volume"] is None  # volume=0 must become None (Pitfall 1)
        assert body["as_of"] == today.isoformat()
    finally:
        cleanup()


def test_bist100_endpoint_single_row_returns_none_change(client):
    today = date.today()
    rows = [_make_commodity_row("XU100.IS", today, close=10000.0, volume=12345.0)]
    cleanup = _override_db_with_rows_map(client, {"XU100.IS": rows})
    try:
        from app.api.market import _market_cache
        _market_cache.clear()
        r = client.get("/api/market/bist100")
        assert r.status_code == 200
        body = r.json()
        assert body["value"] == 10000.0
        assert body["daily_change_pct"] is None
        assert body["volume"] == 12345.0
    finally:
        cleanup()


def test_bist100_endpoint_no_data_returns_503(client):
    cleanup = _override_db_with_rows_map(client, {"XU100.IS": []})
    try:
        from app.api.market import _market_cache
        _market_cache.clear()
        r = client.get("/api/market/bist100")
        assert r.status_code == 503
        assert "BIST100" in r.json()["detail"]
    finally:
        cleanup()


# ─── FOREX TESTS ───


def test_forex_endpoint_returns_pairs_with_computed_change(client):
    today = date.today()
    rows_by_symbol = {
        "USDTRY=X": [
            _make_commodity_row("USDTRY=X", today, close=34.50),
            _make_commodity_row("USDTRY=X", today - timedelta(days=1), close=34.00),
        ],
        "EURTRY=X": [
            _make_commodity_row("EURTRY=X", today, close=37.20),
            _make_commodity_row("EURTRY=X", today - timedelta(days=1), close=37.00),
        ],
        "GBPTRY=X": [_make_commodity_row("GBPTRY=X", today, close=43.10)],  # 1 row only
        "CNYTRY=X": [],  # missing — must be skipped
        "JPYTRY=X": [
            _make_commodity_row("JPYTRY=X", today, close=0.225),
            _make_commodity_row("JPYTRY=X", today - timedelta(days=1), close=0.220),
        ],
        "CHFTRY=X": [
            _make_commodity_row("CHFTRY=X", today, close=39.00),
            _make_commodity_row("CHFTRY=X", today - timedelta(days=1), close=38.50),
        ],
    }
    cleanup = _override_db_with_rows_map(client, rows_by_symbol)
    try:
        from app.api.market import _market_cache
        _market_cache.clear()
        r = client.get("/api/market/forex")
        assert r.status_code == 200
        body = r.json()
        pairs = body["pairs"]
        symbols = {p["symbol"] for p in pairs}
        assert "USDTRY=X" in symbols
        assert "GBPTRY=X" in symbols  # included even with 1 row
        assert "CNYTRY=X" not in symbols  # skipped (no rows)
        assert len(pairs) == 5  # 6 pairs - 1 missing

        usd = next(p for p in pairs if p["symbol"] == "USDTRY=X")
        assert usd["name"] == "USD/TRY"
        assert usd["rate"] == 34.5
        # Pitfall 6: change_pct must be COMPUTED from rows, not read from a field
        assert usd["daily_change_pct"] == round((34.50 - 34.00) / 34.00 * 100, 2)

        gbp = next(p for p in pairs if p["symbol"] == "GBPTRY=X")
        assert gbp["daily_change_pct"] is None  # only 1 row -> None (not 0)
    finally:
        cleanup()


# ─── GOLD TESTS ───


def test_gold_endpoint_computes_all_five_forms(client):
    today = date.today()
    # gold_usd=2400, usdtry=34 -> gram = 2400*34/31.1035 = 2624.06...
    rows_by_symbol = {
        "GC=F": [_make_commodity_row("GC=F", today, close=2400.00)],
        "USDTRY=X": [_make_commodity_row("USDTRY=X", today, close=34.00)],
    }
    cleanup = _override_db_with_rows_map(client, rows_by_symbol)
    try:
        from app.api.market import _market_cache
        _market_cache.clear()
        r = client.get("/api/market/gold")
        assert r.status_code == 200
        body = r.json()
        forms = body["forms"]
        for k in ("gram", "ons", "ceyrek", "yarim", "tam"):
            assert k in forms

        expected_gram = 2400.00 * 34.00 / 31.1035
        assert abs(forms["gram"] - round(expected_gram, 2)) < 0.05
        # ons = gram * 31.1035; tam = gram * 7.016; yarim = gram * 3.508; ceyrek = gram * 1.754
        assert abs(forms["ons"] - round(expected_gram * 31.1035, 2)) < 0.05
        assert abs(forms["tam"] - round(expected_gram * 7.016, 2)) < 0.05
        # Sanity ordering
        assert forms["ons"] > forms["tam"] > forms["yarim"] > forms["ceyrek"] > forms["gram"]

        assert body["gold_usd_per_oz"] == 2400.0
        assert body["usdtry"] == 34.0
    finally:
        cleanup()


def test_gold_endpoint_missing_data_returns_503(client):
    # Only USDTRY=X present, GC=F missing
    today = date.today()
    rows_by_symbol = {
        "GC=F": [],
        "USDTRY=X": [_make_commodity_row("USDTRY=X", today, close=34.00)],
    }
    cleanup = _override_db_with_rows_map(client, rows_by_symbol)
    try:
        from app.api.market import _market_cache
        _market_cache.clear()
        r = client.get("/api/market/gold")
        assert r.status_code == 503
        assert "Altın" in r.json()["detail"]
    finally:
        cleanup()


# ─── STATIC / CONSTANT TESTS ───


@pytest.mark.xfail(reason="DISC-02 endpoint implemented in Plan 28-03", strict=False)
def test_opportunities_endpoint(client):
    """DISC-02: GET /api/market/opportunities returns top BIST100 sorted by overall_score desc."""
    r = client.get("/api/market/opportunities?limit=10")
    assert r.status_code == 200
    body = r.json()
    assert "stocks" in body and "count" in body
    stocks = body["stocks"]
    assert len(stocks) <= 10
    # All must be is_bist100=True implicitly (endpoint filters)
    # Sort check: overall_score descending where present
    scores = [s["overall_score"] for s in stocks if s.get("overall_score") is not None]
    assert scores == sorted(scores, reverse=True), "opportunities not sorted desc by overall_score"


def test_gold_coin_weights_constants():
    """Coin weights are physical constants and must not drift."""
    from app.api.market import GOLD_COIN_WEIGHTS
    assert GOLD_COIN_WEIGHTS["gram"] == 1.0
    assert GOLD_COIN_WEIGHTS["ons"] == 31.1035
    assert GOLD_COIN_WEIGHTS["ceyrek"] == 1.754
    assert GOLD_COIN_WEIGHTS["yarim"] == 3.508
    assert GOLD_COIN_WEIGHTS["tam"] == 7.016


def test_forex_pairs_includes_jpy_chf():
    """Plan 28-01 added JPY/TRY and CHF/TRY; FOREX_PAIRS must expose them."""
    from app.api.market import FOREX_PAIRS
    assert "JPYTRY=X" in FOREX_PAIRS
    assert "CHFTRY=X" in FOREX_PAIRS
    assert FOREX_PAIRS["JPYTRY=X"] == "JPY/TRY"
    assert FOREX_PAIRS["CHFTRY=X"] == "CHF/TRY"
