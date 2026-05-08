"""
Tests for TECH-02 — async yfinance wrappers.

These tests prove:
1. get_ticker_history is an async coroutine function
2. get_ticker_info is an async coroutine function
3. await get_ticker_history returns a DataFrame (executor plumbing works)
4. await get_ticker_info returns a dict (executor plumbing works)
All tests use pytest.mark.asyncio (asyncio_mode=auto in pytest.ini handles this).
"""
import asyncio
import pytest
import pandas as pd
import diskcache
from unittest.mock import patch

import app.services.data_collector as dc


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

