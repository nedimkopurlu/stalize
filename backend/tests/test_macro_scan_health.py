import pytest

from app.services import tcmb_adapter, tuik_adapter


@pytest.mark.asyncio
async def test_run_tuik_scan_marks_success_when_data_found_but_already_persisted(monkeypatch):
    events = []

    async def fake_fetch_cpi():
        return {"inflation_rate_annual": 30.9, "inflation_rate_monthly": None, "url": "https://example.com/cpi"}

    async def fake_fetch_production():
        return {"production_index": 2.2, "month_over_month_change": None, "url": "https://example.com/prod"}

    async def fake_fetch_unemployment():
        return {"unemployment_rate": 8.5, "employment_rate": None, "url": "https://example.com/unemp"}

    async def fake_fetch_capacity():
        return None

    async def fake_store(_event):
        return False

    monkeypatch.setattr(tuik_adapter.tuik_adapter, "fetch_cpi_inflation", fake_fetch_cpi)
    monkeypatch.setattr(tuik_adapter.tuik_adapter, "fetch_industrial_production", fake_fetch_production)
    monkeypatch.setattr(tuik_adapter.tuik_adapter, "fetch_unemployment_rate", fake_fetch_unemployment)
    monkeypatch.setattr(tuik_adapter.tuik_adapter, "fetch_capacity_utilization", fake_fetch_capacity)
    monkeypatch.setattr(tuik_adapter.tuik_adapter, "store_macro_event", fake_store)
    monkeypatch.setattr(tuik_adapter, "record_source_success", lambda source, detail=None: events.append(("success", source, detail)))
    monkeypatch.setattr(tuik_adapter, "record_source_failure", lambda source, error, detail=None: events.append(("failure", source, error, detail)))

    stored = await tuik_adapter.run_tuik_scan()

    assert stored == 0
    assert events == [("success", "tuik", {"fetched_count": 3, "stored_count": 0})]


@pytest.mark.asyncio
async def test_run_tcmb_scan_marks_success_when_data_found_but_already_persisted(monkeypatch):
    events = []

    async def fake_fetch_policy_rate():
        return {"rate": 37.0, "url": "https://example.com/policy"}

    async def fake_fetch_fx_reserves():
        return None

    async def fake_fetch_press_release():
        return {"title": "Faiz Oranlarına İlişkin Basın Duyurusu", "summary": "stub", "interest_rate_decision": True}

    async def fake_store(_event):
        return False

    monkeypatch.setattr(tcmb_adapter.tcmb_adapter, "fetch_policy_rate", fake_fetch_policy_rate)
    monkeypatch.setattr(tcmb_adapter.tcmb_adapter, "fetch_fx_reserves", fake_fetch_fx_reserves)
    monkeypatch.setattr(tcmb_adapter.tcmb_adapter, "fetch_latest_press_release", fake_fetch_press_release)
    monkeypatch.setattr(tcmb_adapter.tcmb_adapter, "store_macro_event", fake_store)
    monkeypatch.setattr(tcmb_adapter, "record_source_success", lambda source, detail=None: events.append(("success", source, detail)))
    monkeypatch.setattr(tcmb_adapter, "record_source_failure", lambda source, error, detail=None: events.append(("failure", source, error, detail)))

    stored = await tcmb_adapter.run_tcmb_scan()

    assert stored == 0
    assert events == [("success", "tcmb", {"fetched_count": 2, "stored_count": 0})]
