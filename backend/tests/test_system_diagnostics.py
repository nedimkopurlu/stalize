"""System diagnostics endpoint tests."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_system_diagnostics_endpoint_shape():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/system/diagnostics")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] in {"healthy", "degraded", "down"}
    assert payload["summary"]["total"] == len(payload["items"])
    assert payload["items"]
    for item in payload["items"]:
        assert item["status"] in {"ok", "warning", "critical"}
        assert item["key"]
        assert item["title"]
        assert item["detail"]
        assert item["remediation"]


@pytest.mark.asyncio
async def test_system_diagnostics_includes_core_checks():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = (await ac.get("/api/system/diagnostics")).json()

    keys = {item["key"] for item in payload["items"]}
    assert {
        "db.stocks",
        "market.price_history",
        "market.reference_data",
        "llm.openai",
        "sources.official",
        "signals.snapshots",
        "signals.outcomes",
        "strategy.backtest",
        "risk.alerts",
        "scheduler.jobs",
    }.issubset(keys)
