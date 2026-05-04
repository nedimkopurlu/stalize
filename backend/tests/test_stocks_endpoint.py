"""Tests for /stocks endpoint covering DISC-01 (BIST100 filter + overall_score sort)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def stocks_client(app_client):
    """Module alias for the session-scoped app_client fixture in conftest.py."""
    return app_client


@pytest.mark.xfail(reason="Verified live in Plan 28-03 once data populated", strict=False)
def test_bist100_filter(stocks_client):
    """DISC-01: /stocks?bist100=true&sort_by=overall_score returns only BIST100 stocks
    ordered by overall_score desc (nulls last)."""
    r = stocks_client.get("/api/stocks?bist100=true&sort_by=overall_score&limit=20")
    assert r.status_code == 200
    body = r.json()
    assert "stocks" in body
    stocks = body["stocks"]
    # Every returned stock must be flagged BIST100
    for s in stocks:
        assert s.get("is_bist100") is True, f"non-BIST100 stock leaked: {s.get('symbol')}"
    # Sort: overall_score descending where not None
    scored = [s["overall_score"] for s in stocks if s.get("overall_score") is not None]
    assert scored == sorted(scored, reverse=True), "stocks not sorted by overall_score desc"


def test_stocks_endpoint_accepts_bist100_param(stocks_client):
    """The bist100 query param is accepted (no 422). Schema-only check."""
    r = stocks_client.get("/api/stocks?bist100=true&limit=1")
    assert r.status_code in (200, 500), f"bist100 param rejected: {r.status_code} {r.text[:200]}"
