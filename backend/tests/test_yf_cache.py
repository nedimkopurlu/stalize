"""
Tests for MLCA-02 — yfinance result-level caching via diskcache.
All tests mock yf.Ticker; no real HTTP calls are made.

Updated for TECH-02: get_ticker_history / get_ticker_info are now async;
tests use async def + await to match the new async signatures.
"""
import pytest
import pandas as pd
import diskcache
from unittest.mock import patch


def make_price_df():
    """Minimal non-empty DataFrame matching yfinance history output."""
    return pd.DataFrame(
        {"Close": [100.0, 101.0], "Volume": [1000, 1100]},
        index=pd.date_range("2026-04-17", periods=2)
    )


async def test_price_cache_hit(tmp_path):
    """Second call returns cached result; yf.Ticker called only once."""
    import app.services.data_collector as dc

    # Use a fresh diskcache in tmp_path to isolate this test
    test_cache = diskcache.Cache(str(tmp_path / "yf_test"))
    with patch.object(dc, "_yf_cache", test_cache):
        with patch("app.services.data_collector.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = make_price_df()
            await dc.get_ticker_history("AKBNK.IS", "5d")  # first call — cache miss
            await dc.get_ticker_history("AKBNK.IS", "5d")  # second call — cache hit
            # yf.Ticker should have been called exactly once (first call only)
            assert mock_ticker.call_count == 1


async def test_price_cache_ttl(tmp_path):
    """Price data is cached with expire=300 (5 minutes)."""
    import app.services.data_collector as dc

    test_cache = diskcache.Cache(str(tmp_path / "yf_ttl"))
    set_calls = []

    original_set = test_cache.set

    def capturing_set(key, value, **kwargs):
        set_calls.append(kwargs.get("expire"))
        return original_set(key, value, **kwargs)

    test_cache.set = capturing_set

    with patch.object(dc, "_yf_cache", test_cache):
        with patch("app.services.data_collector.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = make_price_df()
            await dc.get_ticker_history("AKBNK.IS", "5d")

    assert len(set_calls) == 1
    assert set_calls[0] == 300


async def test_info_cache_ttl(tmp_path):
    """Fundamental (info) data is cached with expire=86400 (24 hours)."""
    import app.services.data_collector as dc

    test_cache = diskcache.Cache(str(tmp_path / "yf_info_ttl"))
    set_calls = []

    original_set = test_cache.set

    def capturing_set(key, value, **kwargs):
        set_calls.append(kwargs.get("expire"))
        return original_set(key, value, **kwargs)

    test_cache.set = capturing_set

    with patch.object(dc, "_yf_cache", test_cache):
        with patch("app.services.data_collector.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.info = {"sector": "Finance", "marketCap": 1e10}
            await dc.get_ticker_info("AKBNK.IS")

    assert len(set_calls) == 1
    assert set_calls[0] == 86400


async def test_empty_not_cached(tmp_path):
    """Empty DataFrame from yfinance is NOT written to cache (Yahoo error guard)."""
    import app.services.data_collector as dc

    test_cache = diskcache.Cache(str(tmp_path / "yf_empty"))
    with patch.object(dc, "_yf_cache", test_cache):
        with patch("app.services.data_collector.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = pd.DataFrame()  # empty
            await dc.get_ticker_history("BADTICKER.IS", "5d")
            # Nothing should be in cache
            assert test_cache.get("history:BADTICKER.IS:5d") is None
