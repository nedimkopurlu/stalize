"""
Tests for Phase 35-01: OpenAI-backed GeminiService alias — SDK integration and fallback.
Requirement: LLM-01
"""
import pytest
from unittest.mock import AsyncMock, MagicMock


# ---------------------------------------------------------------------------
# Test 1: Success path — generate() returns the model's text
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_generate_success():
    """
    When OpenAI chat completions returns message content,
    generate() must return that text unchanged.
    """
    from app.services.gemini_service import GeminiService, FALLBACK_MESSAGE

    mock_choice = MagicMock()
    mock_choice.message.content = "Analiz metni"
    mock_response = MagicMock(choices=[mock_choice])
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    service = GeminiService()
    service._configured = True
    service._client = mock_client
    result = await service.generate("Test prompt")

    assert result == "Analiz metni", f"Expected 'Analiz metni', got {result!r}"


# ---------------------------------------------------------------------------
# Test 2: Provider error must return FALLBACK_MESSAGE
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_generate_provider_error():
    """
    When the OpenAI SDK raises an exception,
    generate() must return FALLBACK_MESSAGE without re-raising.
    """
    from app.services.gemini_service import GeminiService, FALLBACK_MESSAGE

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=Exception("quota exceeded"))

    service = GeminiService()
    service._configured = True
    service._client = mock_client
    result = await service.generate("Test prompt")

    assert result == FALLBACK_MESSAGE, (
        f"Expected fallback on 429, got {result!r}"
    )


# ---------------------------------------------------------------------------
# Test 3: Empty response — return FALLBACK_MESSAGE
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_generate_empty_response():
    """
    When the model returns empty content, generate() must return FALLBACK_MESSAGE.
    """
    from app.services.gemini_service import GeminiService, FALLBACK_MESSAGE

    mock_choice = MagicMock()
    mock_choice.message.content = ""
    mock_response = MagicMock(choices=[mock_choice])
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    service = GeminiService()
    service._configured = True
    service._client = mock_client
    result = await service.generate("Test prompt")

    assert result == FALLBACK_MESSAGE, (
        f"Expected fallback on generic exception, got {result!r}"
    )


# ---------------------------------------------------------------------------
# Test 4: No API key/client — generate() returns FALLBACK_MESSAGE immediately
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_generate_no_api_key(monkeypatch):
    """
    When OPENAI_API_KEY is None, generate() must return FALLBACK_MESSAGE
    without making any SDK call.
    """
    from app.core.config import settings
    from app.services.gemini_service import FALLBACK_MESSAGE

    # Ensure settings has no API key for this test
    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)

    # Re-instantiate with no key (no genai.configure() call)
    from app.services.gemini_service import GeminiService
    service = GeminiService()

    result = await service.generate("Test prompt")

    assert result == FALLBACK_MESSAGE, (
        f"Expected fallback when no API key, got {result!r}"
    )
