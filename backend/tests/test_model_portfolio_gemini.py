"""Phase 39: _generate_gemini_rationale() unit testleri — LLM-04 doğrulaması."""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_gemini_rationale_with_changes():
    """Eklenen/çıkarılan hisseler varsa prompt bunları içerir ve Gemini çıktısı döner."""
    changes = {"added": ["THYAO", "GARAN"], "removed": ["EREGL"], "increased": [], "decreased": [], "unchanged": []}
    mock_response = "Bu hafta model portföy iki hisse ekledi, bir hisseyi çıkardı."

    with patch(
        "app.services.model_portfolio.gemini_service.generate",
        new=AsyncMock(return_value=mock_response),
    ):
        from app.services.model_portfolio import _generate_gemini_rationale
        result = await _generate_gemini_rationale(changes, 10)

    assert result == mock_response


@pytest.mark.asyncio
async def test_gemini_rationale_no_changes():
    """Değişiklik yoksa prompt 'büyük değişiklik yapılmadı' içerir."""
    changes = {"added": [], "removed": [], "increased": [], "decreased": [], "unchanged": []}
    captured: list[str] = []

    async def capture_prompt(prompt: str) -> str:
        captured.append(prompt)
        return "Portföy dengede kaldı."

    with patch(
        "app.services.model_portfolio.gemini_service.generate",
        new=AsyncMock(side_effect=capture_prompt),
    ):
        from app.services.model_portfolio import _generate_gemini_rationale
        result = await _generate_gemini_rationale(changes, 8)

    assert "büyük değişiklik" in captured[0]
    assert result == "Portföy dengede kaldı."


@pytest.mark.asyncio
async def test_gemini_rationale_returns_fallback():
    """Quota dolunca FALLBACK_MESSAGE döner — bu normal bir durum."""
    from app.services.gemini_service import FALLBACK_MESSAGE

    with patch(
        "app.services.model_portfolio.gemini_service.generate",
        new=AsyncMock(return_value=FALLBACK_MESSAGE),
    ):
        from app.services.model_portfolio import _generate_gemini_rationale
        result = await _generate_gemini_rationale({"added": [], "removed": []}, 5)

    assert result == FALLBACK_MESSAGE
    # Caller FALLBACK_MESSAGE gelince deterministik özeti kullanır
    assert FALLBACK_MESSAGE in result
