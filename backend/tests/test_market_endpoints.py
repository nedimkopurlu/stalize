"""Tests for /market/* endpoints (Phase 28). Plan 28-01 ships the scaffolding;
Plan 28-02 implements bist100/forex/gold; Plan 28-03 implements opportunities."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client(app_client):
    """Module alias for the session-scoped app_client fixture in conftest.py."""
    return app_client


def test_market_router_mounted(client):
    """Plan 28-01: market router must be mounted under /api."""
    r = client.get("/api/market/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("router") == "market"
    assert body.get("status") == "ok"


@pytest.mark.xfail(reason="DASH-01 endpoint implemented in Plan 28-02", strict=False)
def test_bist100_endpoint(client):
    """DASH-01: GET /api/market/bist100 returns value, daily_change_pct, volume, as_of."""
    r = client.get("/api/market/bist100")
    # 200 if data is present in DB; 503 only if no XU100.IS rows exist (acceptable in CI)
    assert r.status_code in (200, 503)
    if r.status_code == 200:
        body = r.json()
        assert "value" in body
        assert "daily_change_pct" in body
        assert "volume" in body
        assert "as_of" in body
        assert isinstance(body["value"], (int, float))


@pytest.mark.xfail(reason="DASH-02 endpoint implemented in Plan 28-02", strict=False)
def test_forex_endpoint(client):
    """DASH-02: GET /api/market/forex returns >=5 TRY pairs with rate + daily_change_pct."""
    r = client.get("/api/market/forex")
    assert r.status_code == 200
    body = r.json()
    assert "pairs" in body
    pairs = body["pairs"]
    assert isinstance(pairs, list)
    assert len(pairs) >= 5, f"expected >=5 pairs, got {len(pairs)}"
    for p in pairs:
        assert "symbol" in p and "name" in p and "rate" in p
        assert p["name"].endswith("/TRY") or p["name"] == "DXY"


@pytest.mark.xfail(reason="DASH-03 endpoint implemented in Plan 28-02", strict=False)
def test_gold_endpoint(client):
    """DASH-03: GET /api/market/gold returns all 5 forms (gram, ons, ceyrek, yarim, tam) in TRY."""
    r = client.get("/api/market/gold")
    assert r.status_code in (200, 503)
    if r.status_code == 200:
        body = r.json()
        assert "forms" in body
        forms = body["forms"]
        for key in ("gram", "ons", "ceyrek", "yarim", "tam"):
            assert key in forms, f"missing gold form: {key}"
            assert isinstance(forms[key], (int, float))
        # Sanity: ons > tam > yarim > ceyrek > gram (in TRY)
        assert forms["ons"] > forms["tam"] > forms["yarim"] > forms["ceyrek"] > forms["gram"]


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
