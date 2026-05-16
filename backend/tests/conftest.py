"""Shared test fixtures for Phase 1 Foundation Repair tests."""
import asyncio
import os
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("RUN_FULL_INITIAL_LOAD_ON_STARTUP", "false")


@pytest.fixture(scope="session")
def app_client():
    """Session-scoped TestClient shared across all test modules.

    A single TestClient start/stop per pytest session avoids the APScheduler
    + asyncpg event-loop collision that occurs when two test modules each create
    their own TestClient instances sequentially.
    """
    from app.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def event_loop():
    """Session-scoped event loop so asyncpg connections are not cross-loop.

    Without this, each async test gets its own event loop. SQLAlchemy's async
    pool holds asyncpg connections bound to the first event loop; when a second
    test runs with a new loop those connections raise 'Future attached to a
    different loop'. A session loop keeps all async tests on the same loop so
    the pool stays valid throughout the test run.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """
    Returns a mock Settings object with the authoritative weights from config.py.
    Use this to test that scoring.py reads from settings, not hardcoded BASE_WEIGHTS.
    """
    s = MagicMock()
    s.WEIGHT_FUNDAMENTAL = 0.45
    s.WEIGHT_TECHNICAL = 0.40
    s.WEIGHT_NEWS = 0.15
    return s


@pytest.fixture
def mock_stock():
    """
    Returns a mock Stock ORM instance with all scoring-relevant fields set to neutral values.
    macro_score is intentionally absent (getattr fallback test).
    """
    stock = MagicMock()
    stock.technical_score = 60.0
    stock.fundamental_score = 55.0
    stock.sentiment_score = 50.0
    # macro_score deliberately NOT set — tests getattr(stock, "macro_score", None) behavior
    del stock.macro_score  # MagicMock: accessing undefined attr raises AttributeError
    return stock


@pytest.fixture
def mock_stock_with_macro(mock_stock):
    """Stock that has a macro_score value."""
    mock_stock.macro_score = 48.0
    return mock_stock
