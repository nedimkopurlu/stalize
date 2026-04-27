import pytest
from datetime import date
from unittest.mock import AsyncMock

from app.services import tefas_snapshot
from app.services.tefas_snapshot import (
    ensure_fresh_tefas_snapshot,
    persist_tefas_universe_snapshot,
    tefas_snapshot_is_stale,
)
from datetime import datetime, timedelta


def test_tefas_snapshot_payload_can_be_persisted_shape():
    payload = {
        "fund_types": [
            {
                "fund_type": "YAT",
                "fund_type_label": "Menkul Kıymet Yatırım Fonları",
                "items": [
                    {
                        "fund_code": "AFT",
                        "fund_name": "Ak Portfoy Teknoloji",
                        "umbrella_type": "Hisse Senedi Şemsiye Fonu",
                        "one_month_return_pct": 4.22,
                        "detail_url": "https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod=AFT",
                    }
                ],
            }
        ]
    }

    rows = []
    for fund_type_payload in payload["fund_types"]:
        for item in fund_type_payload["items"]:
            rows.append(
                {
                    "snapshot_date": date(2026, 4, 24),
                    "fund_code": item["fund_code"],
                    "fund_name": item["fund_name"],
                    "fund_type": fund_type_payload["fund_type"],
                    "fund_type_label": fund_type_payload["fund_type_label"],
                    "umbrella_type": item["umbrella_type"],
                    "detail_url": item["detail_url"],
                }
            )

    assert len(rows) == 1
    assert rows[0]["fund_code"] == "AFT"
    assert rows[0]["fund_type"] == "YAT"


@pytest.mark.asyncio
async def test_persist_tefas_universe_snapshot_returns_row_count(monkeypatch):
    payload = {
        "fund_types": [
            {
                "fund_type": "YAT",
                "fund_type_label": "Menkul Kıymet Yatırım Fonları",
                "items": [
                    {"fund_code": "AFT", "fund_name": "Ak Portfoy", "detail_url": "https://example.com/AFT"},
                    {"fund_code": "AFA", "fund_name": "Ak Portfoy Amerika", "detail_url": "https://example.com/AFA"},
                ],
            }
        ]
    }

    class FakeSession:
        def __init__(self):
            self.added = []
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False
        async def execute(self, _stmt):
            return None
        def add_all(self, rows):
            self.added.extend(rows)
        async def commit(self):
            return None

    fake_session = FakeSession()
    monkeypatch.setattr(tefas_snapshot, "AsyncSessionLocal", lambda: fake_session)

    stored = await persist_tefas_universe_snapshot(payload, snapshot_date=date(2026, 4, 24))

    assert stored == 2
    assert len(fake_session.added) == 2


def test_tefas_snapshot_is_stale_for_old_dates():
    old_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
    recent_date = datetime.now().strftime("%Y-%m-%d")
    assert tefas_snapshot_is_stale(old_date, max_age_days=1) is True
    assert tefas_snapshot_is_stale(recent_date, max_age_days=1) is False


@pytest.mark.asyncio
async def test_ensure_fresh_tefas_snapshot_refreshes_when_stale(monkeypatch):
    old_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
    recent_date = datetime.now().strftime("%Y-%m-%d")
    
    monkeypatch.setattr(
        tefas_snapshot,
        "get_latest_tefas_snapshot",
        AsyncMock(
            side_effect=[
                {"snapshot_date": old_date, "count": 1, "items": [{"fund_code": "OLD"}]},
                {"snapshot_date": recent_date, "count": 1, "items": [{"fund_code": "NEW"}]},
            ]
        ),
    )

    refresh_calls = []

    async def fake_runner():
        refresh_calls.append("ran")
        return 1

    monkeypatch.setattr(tefas_snapshot, "_get_tefas_runner", lambda: fake_runner)

    payload = await ensure_fresh_tefas_snapshot(limit=5)

    assert refresh_calls == ["ran"]
    assert payload["auto_refresh_attempted"] is True
    assert payload["auto_refresh_performed"] is True
    assert payload["is_stale"] is False
    assert payload["items"][0]["fund_code"] == "NEW"
