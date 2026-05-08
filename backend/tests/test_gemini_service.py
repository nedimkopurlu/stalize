"""
Tests for Phase 35-01: GeminiService — SDK integration, async generate, quota fallback.
Requirement: LLM-01
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ---------------------------------------------------------------------------
# Test 1: Success path — generate() returns the model's text
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_generate_success():
    """
    When generate_content_async returns a response with .text,
    generate() must return that text unchanged.
    """
    from app.services.gemini_service import GeminiService, FALLBACK_MESSAGE

    mock_response = MagicMock()
    mock_response.text = "Analiz metni"

    with patch(
        "google.generativeai.GenerativeModel.generate_content_async",
        new=AsyncMock(return_value=mock_response),
    ):
        service = GeminiService()
        # Force _configured=True so SDK path is exercised
        service._configured = True
        result = await service.generate("Test prompt")

    assert result == "Analiz metni", f"Expected 'Analiz metni', got {result!r}"


# ---------------------------------------------------------------------------
# Test 2: Quota / 429 — ResourceExhausted must return FALLBACK_MESSAGE
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_generate_quota_exhausted():
    """
    When generate_content_async raises ResourceExhausted (HTTP 429),
    generate() must return FALLBACK_MESSAGE without re-raising.
    """
    from app.services.gemini_service import GeminiService, FALLBACK_MESSAGE
    from google.api_core.exceptions import ResourceExhausted

    with patch(
        "google.generativeai.GenerativeModel.generate_content_async",
        new=AsyncMock(side_effect=ResourceExhausted("quota exceeded")),
    ):
        service = GeminiService()
        service._configured = True
        result = await service.generate("Test prompt")

    assert result == FALLBACK_MESSAGE, (
        f"Expected fallback on 429, got {result!r}"
    )


# ---------------------------------------------------------------------------
# Test 3: Generic exception — any other error must return FALLBACK_MESSAGE
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_generate_generic_exception():
    """
    When generate_content_async raises a generic Exception (e.g. network error),
    generate() must return FALLBACK_MESSAGE without re-raising.
    """
    from app.services.gemini_service import GeminiService, FALLBACK_MESSAGE

    with patch(
        "google.generativeai.GenerativeModel.generate_content_async",
        new=AsyncMock(side_effect=Exception("network error")),
    ):
        service = GeminiService()
        service._configured = True
        result = await service.generate("Test prompt")

    assert result == FALLBACK_MESSAGE, (
        f"Expected fallback on generic exception, got {result!r}"
    )


# ---------------------------------------------------------------------------
# Test 4: No API key — generate() returns FALLBACK_MESSAGE immediately
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_generate_no_api_key(monkeypatch):
    """
    When GEMINI_API_KEY is None, generate() must return FALLBACK_MESSAGE
    without making any SDK call.
    """
    from app.core.config import settings
    from app.services.gemini_service import FALLBACK_MESSAGE

    # Ensure settings has no API key for this test
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)

    # Re-instantiate with no key (no genai.configure() call)
    from app.services.gemini_service import GeminiService
    service = GeminiService()

    result = await service.generate("Test prompt")

    assert result == FALLBACK_MESSAGE, (
        f"Expected fallback when no API key, got {result!r}"
    )
