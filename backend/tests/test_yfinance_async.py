"""
Tests for TECH-02 — async yfinance wrappers and non-blocking macro endpoint.

These tests prove:
1. get_ticker_history is an async coroutine function
2. get_ticker_info is an async coroutine function
3. await get_ticker_history returns a DataFrame (executor plumbing works)
4. await get_ticker_info returns a dict (executor plumbing works)
5. /api/macro/indicators offloads yf.download to a thread (not MainThread)

All tests use pytest.mark.asyncio (asyncio_mode=auto in pytest.ini handles this).
"""
import asyncio
import threading
import pytest
import pandas as pd
import diskcache
from unittest.mock import patch, MagicMock

import app.services.data_collector as dc
import app.api.macro as macro_module


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def make_price_df():
    """Minimal non-empty DataFrame matching yfinance history output."""
    return pd.DataFrame(
        {"Close": [100.0, 101.0], "Volume": [1000, 1100]},
        index=pd.date_range("2026-04-17", periods=2),
    )


# ─── TEST 1: get_ticker_history is a coroutine function ──────────────────────

def test_get_ticker_history_is_coroutine():
    """get_ticker_history must be an async function (coroutine function)."""
    assert asyncio.iscoroutinefunction(dc.get_ticker_history), (
        "get_ticker_history is not async — must be converted to "
        "async def with run_in_executor for the yfinance HTTP call"
    )


# ─── TEST 2: get_ticker_info is a coroutine function ─────────────────────────

def test_get_ticker_info_is_coroutine():
    """get_ticker_info must be an async function (coroutine function)."""
    assert asyncio.iscoroutinefunction(dc.get_ticker_info), (
        "get_ticker_info is not async — must be converted to "
        "async def with run_in_executor for the yfinance HTTP call"
    )


# ─── TEST 3: await get_ticker_history returns a DataFrame ────────────────────

@pytest.mark.asyncio
async def test_get_ticker_history_awaitable_returns_dataframe(tmp_path):
    """
    Monkeypatch yf.Ticker so no real HTTP call is made.
    Awaiting get_ticker_history must return the stubbed DataFrame.
    """
    stub_df = make_price_df()
    test_cache = diskcache.Cache(str(tmp_path / "yf_hist_test"))

    with patch.object(dc, "_yf_cache", test_cache):
        with patch("app.services.data_collector.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = stub_df
            result = await dc.get_ticker_history("TEST.IS", period="5d")

    assert isinstance(result, pd.DataFrame), (
        f"Expected DataFrame, got {type(result)}"
    )
    assert not result.empty, "Returned DataFrame must not be empty"
    assert list(result.columns) == ["Close", "Volume"]


# ─── TEST 4: await get_ticker_info returns a dict ────────────────────────────

@pytest.mark.asyncio
async def test_get_ticker_info_awaitable_returns_dict(tmp_path):
    """
    Monkeypatch yf.Ticker so no real HTTP call is made.
    Awaiting get_ticker_info must return the stubbed dict.
    """
    stub_info = {"sector": "Finance", "marketCap": 1_000_000_000}
    test_cache = diskcache.Cache(str(tmp_path / "yf_info_test"))

    with patch.object(dc, "_yf_cache", test_cache):
        with patch("app.services.data_collector.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.info = stub_info
            result = await dc.get_ticker_info("TEST.IS")

    assert isinstance(result, dict), (
        f"Expected dict, got {type(result)}"
    )
    assert result.get("sector") == "Finance"
    assert result.get("marketCap") == 1_000_000_000


# ─── TEST 5: /api/macro/indicators offloads HTTP fallback to thread ───────────

@pytest.mark.asyncio
async def test_macro_indicators_uses_executor():
    """
    Force the DB-first macro endpoint to miss and use the requests fallback.
    Monkeypatch requests.get to record which thread it runs in.
    The /api/macro/indicators endpoint must offload the blocking HTTP call via
    run_in_executor so it runs on a worker thread (not MainThread).

    Also asserts the response shape contains the expected keys.

    Note (v1.2): _fetch_last_close_with_date was rewritten to use requests.get
    directly (Yahoo Finance JSON API) instead of yf.Ticker.history. The
    run_in_executor guarantee still holds — this test patches requests.get.
    """
    import httpx
    import json
    import requests as requests_lib
    from app.main import app as fastapi_app

    # Track which thread the blocking HTTP call runs in
    recorded_thread_name: list[str] = []

    # Build a minimal Yahoo Finance JSON response
    _ts = 1745568000  # 2026-04-25
    _stub_payload = {
        "chart": {
            "result": [{
                "timestamp": [_ts],
                "indicators": {"quote": [{"close": [32.0]}]},
            }]
        }
    }

    class _StubResponse:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return _stub_payload

    def stub_requests_get(*args, **kwargs):
        recorded_thread_name.append(threading.current_thread().name)
        return _StubResponse()

    async def stub_latest_market_reading(symbol: str):
        return None, None

    # Reset the 60s TTL cache so the endpoint does a fresh fetch
    macro_module._indicators_cache.clear()

    with patch.object(macro_module, "_latest_market_reading", side_effect=stub_latest_market_reading):
        with patch("app.api.macro.requests.get", side_effect=stub_requests_get):
            transport = httpx.ASGITransport(app=fastapi_app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://testserver"
            ) as client:
                response = await client.get("/api/macro/indicators")

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )

    # Assert thread offload: HTTP call must NOT run on MainThread
    assert len(recorded_thread_name) == 3, (
        f"requests.get should be called once per symbol (3 total), got: {recorded_thread_name}"
    )
    assert all(name != "MainThread" for name in recorded_thread_name), (
        f"requests.get ran on main thread: {recorded_thread_name!r}. "
        "The endpoint must use run_in_executor to offload the blocking call."
    )

    # Assert response shape
    data = response.json()
    for key in ("usdtry", "gold_try", "bist100", "interest_rate", "inflation_rate", "as_of"):
        assert key in data, f"Response missing key: {key!r}. Got: {list(data.keys())}"
