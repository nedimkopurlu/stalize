"""Tests for PATCH /portfolio/positions/{id}/close — PORT-02"""
import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.security import verify_api_key
from app.core.database import get_db


def _make_position(id_=1, symbol="THYAO", entry_price=100.0, quantity=10.0, is_active=True):
    """Helper to create a mock PortfolioPosition."""
    pos = MagicMock()
    pos.id = id_
    pos.symbol = symbol
    pos.entry_price = entry_price
    pos.quantity = quantity
    pos.is_active = is_active
    pos.exit_price = None
    pos.exit_date = None
    pos.realized_pnl = None
    return pos


def _make_fake_db(position=None):
    """Returns an async generator that yields a mock DB session."""
    async def _fake_db():
        db = MagicMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.flush = AsyncMock()

        fake_result = MagicMock()
        fake_result.scalar_one_or_none = MagicMock(return_value=position)
        fake_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))

        db.execute = AsyncMock(return_value=fake_result)
        yield db

    return _fake_db


@pytest.mark.asyncio
async def test_close_position_success():
    """PATCH with valid exit_price and exit_date → 200 with correct shape."""
    pos = _make_position(id_=1, symbol="THYAO", entry_price=100.0, quantity=10.0)

    app.dependency_overrides[verify_api_key] = lambda: None
    app.dependency_overrides[get_db] = _make_fake_db(position=pos)

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.patch(
                "/api/portfolio/positions/1/close",
                json={"exit_price": 120.0, "exit_date": "2026-05-08"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert data["symbol"] == "THYAO"
    assert data["status"] == "closed"
    # realized_pnl = (120.0 - 100.0) * 10.0 = 200.0
    assert data["realized_pnl"] == 200.0


@pytest.mark.asyncio
async def test_close_position_realized_pnl_calculation():
    """realized_pnl = round((exit_price - entry_price) * quantity, 4)."""
    pos = _make_position(id_=2, symbol="AKBNK", entry_price=45.3, quantity=100.0)

    app.dependency_overrides[verify_api_key] = lambda: None
    app.dependency_overrides[get_db] = _make_fake_db(position=pos)

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.patch(
                "/api/portfolio/positions/2/close",
                json={"exit_price": 50.75, "exit_date": "2026-05-08"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    expected_pnl = round((50.75 - 45.3) * 100.0, 4)
    assert abs(data["realized_pnl"] - expected_pnl) < 0.0001


@pytest.mark.asyncio
async def test_close_position_not_found():
    """PATCH with non-existent or already-closed position → 404."""
    app.dependency_overrides[verify_api_key] = lambda: None
    app.dependency_overrides[get_db] = _make_fake_db(position=None)  # not found

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.patch(
                "/api/portfolio/positions/999/close",
                json={"exit_price": 120.0, "exit_date": "2026-05-08"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert "bulunamadı" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_close_position_wrong_api_key():
    """PATCH with wrong API key when API_KEY is configured → 401."""
    from unittest.mock import patch as mock_patch
    from app.core import config as cfg

    # Temporarily set a real API_KEY so verify_api_key rejects wrong keys
    original_key = cfg.settings.API_KEY
    try:
        cfg.settings.API_KEY = "super-secret-key"
        app.dependency_overrides.clear()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.patch(
                "/api/portfolio/positions/1/close",
                headers={"X-API-Key": "wrong-key"},
                json={"exit_price": 120.0, "exit_date": "2026-05-08"},
            )

        assert resp.status_code == 401
        assert "Invalid" in resp.json()["detail"] or "missing" in resp.json()["detail"]
    finally:
        cfg.settings.API_KEY = original_key
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_close_position_invalid_price_zero():
    """PATCH with exit_price=0 → 422 (validation error)."""
    pos = _make_position(id_=1, symbol="THYAO", entry_price=100.0, quantity=10.0)

    app.dependency_overrides[verify_api_key] = lambda: None
    app.dependency_overrides[get_db] = _make_fake_db(position=pos)

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.patch(
                "/api/portfolio/positions/1/close",
                json={"exit_price": 0, "exit_date": "2026-05-08"},
            )
    finally:
        app.dependency_overrides.clear()

    # exit_price=0 → _validate_positive_number raises HTTPException(422)
    assert resp.status_code == 422
