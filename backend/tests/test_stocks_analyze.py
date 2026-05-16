"""Tests for POST /stocks/{symbol}/analyze endpoint."""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from app.main import app

MOCK_ANALYSIS = "AKBNK için OpenAI analizi: Güçlü finansal göstergeler."


@pytest.mark.asyncio
async def test_analyze_returns_expected_shape():
    """POST /stocks/AKBNK/analyze returns 200 with correct keys and values."""
    with patch("app.api.stocks.gemini_service.generate", new=AsyncMock(return_value=MOCK_ANALYSIS)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/stocks/AKBNK/analyze")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "AKBNK"
    assert data["analysis"] == MOCK_ANALYSIS
    assert data["cached"] is False
    assert "generated_at" in data


@pytest.mark.asyncio
async def test_analyze_nonexistent_stock_returns_404():
    """POST /stocks/NONEXISTENT_XYZ/analyze returns 404."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/stocks/NONEXISTENT_XYZ/analyze")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_analyze_fallback_returns_200():
    """Endpoint still returns 200 when gemini_service returns FALLBACK_MESSAGE."""
    from app.services.gemini_service import FALLBACK_MESSAGE
    with patch("app.api.stocks.gemini_service.generate", new=AsyncMock(return_value=FALLBACK_MESSAGE)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/stocks/AKBNK/analyze")
    assert resp.status_code == 200
    assert resp.json()["analysis"] == FALLBACK_MESSAGE


@pytest.mark.asyncio
async def test_analyze_generated_at_is_iso8601():
    """generated_at field is a valid ISO8601 datetime string."""
    from datetime import datetime
    with patch("app.api.stocks.gemini_service.generate", new=AsyncMock(return_value=MOCK_ANALYSIS)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/stocks/AKBNK/analyze")
    data = resp.json()
    assert "generated_at" in data
    # Validate ISO8601 — datetime.fromisoformat will raise ValueError if invalid
    generated_at = data["generated_at"].replace("Z", "+00:00")
    parsed = datetime.fromisoformat(generated_at)
    assert parsed is not None
