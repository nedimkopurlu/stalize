"""Tests for GET /intelligence/daily-summary — cache hit/miss behaviour."""
import datetime
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

import app.api.intelligence as intel_module


@pytest.fixture(autouse=True)
def clear_cache():
    """Reset the in-memory cache before and after every test."""
    intel_module._summary_cache.clear()
    yield
    intel_module._summary_cache.clear()


@pytest.mark.asyncio
async def test_cache_miss_calls_gemini():
    """Cache-miss path: gemini_service.generate is called and from_cache is False."""
    mock_generate = AsyncMock(return_value="Bugün BIST100 yükseliş eğiliminde.")
    fake_gemini = MagicMock()
    fake_gemini.generate = mock_generate
    fake_module = MagicMock()
    fake_module.gemini_service = fake_gemini

    orig = sys.modules.get("app.services.gemini_service")
    sys.modules["app.services.gemini_service"] = fake_module
    try:
        result = await intel_module.get_daily_summary()
    finally:
        if orig is None:
            sys.modules.pop("app.services.gemini_service", None)
        else:
            sys.modules["app.services.gemini_service"] = orig

    assert result["from_cache"] is False
    assert result["summary"] != ""
    mock_generate.assert_called_once()


@pytest.mark.asyncio
async def test_cache_hit_skips_gemini():
    """Cache-hit path: when today's summary is already cached, generate is not called."""
    today = datetime.date.today().isoformat()
    intel_module._summary_cache["date"] = today
    intel_module._summary_cache["summary"] = "Önbellekten özet."
    intel_module._summary_cache["generated_at"] = "2026-05-08T06:00:00+00:00"

    mock_generate = AsyncMock()
    fake_gemini = MagicMock()
    fake_gemini.generate = mock_generate
    fake_module = MagicMock()
    fake_module.gemini_service = fake_gemini

    orig = sys.modules.get("app.services.gemini_service")
    sys.modules["app.services.gemini_service"] = fake_module
    try:
        result = await intel_module.get_daily_summary()
    finally:
        if orig is None:
            sys.modules.pop("app.services.gemini_service", None)
        else:
            sys.modules["app.services.gemini_service"] = orig

    assert result["from_cache"] is True
    assert result["summary"] == "Önbellekten özet."
    mock_generate.assert_not_called()


@pytest.mark.asyncio
async def test_gemini_error_returns_fallback_not_500():
    """When Gemini raises, endpoint returns a fallback string — never a 500."""
    async def _failing_generate(*args, **kwargs):
        raise RuntimeError("Gemini quota exceeded")

    intel_module._summary_cache.clear()

    fake_gemini = MagicMock()
    fake_gemini.generate = _failing_generate
    fake_module = MagicMock()
    fake_module.gemini_service = fake_gemini

    orig = sys.modules.get("app.services.gemini_service")
    sys.modules["app.services.gemini_service"] = fake_module
    try:
        result = await intel_module.get_daily_summary()
    finally:
        if orig is None:
            sys.modules.pop("app.services.gemini_service", None)
        else:
            sys.modules["app.services.gemini_service"] = orig

    assert "summary" in result
    assert result["summary"]  # non-empty fallback text
    assert result["from_cache"] is False
