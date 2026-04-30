import pytest
from fastapi import HTTPException
from datetime import datetime, timezone

from app.api import admin
from app.api.admin import (
    archive_bist_datastore_latest_files,
    backfill_bist_datastore_snapshot,
    get_bist_datastore_archive,
    get_bist_datastore_catalog,
    get_bist_datastore_latest_snapshot,
    get_bist_datastore_product_files,
    get_borsa_istanbul_announcements,
    get_hmb_publications,
    get_source_catalog,
    get_source_health_dashboard,
    get_source_health_history_endpoint,
    get_tefas_fund_detail,
    get_tefas_universe,
    health_check,
    trigger_source_scan,
)
from app.data.official_sources import OFFICIAL_SOURCE_CATALOG, get_official_source_keys
from app.services.official_ingest import is_source_active
from app.services.bist_datastore_adapter import bist_datastore_adapter
from app.services.borsa_announcements import borsa_announcements_adapter
from app.services.hmb_adapter import hmb_adapter
from app.services.tefas_adapter import tefas_adapter


def test_official_source_catalog_keys_are_unique():
    keys = get_official_source_keys()
    assert len(keys) == len(set(keys))


def test_official_source_catalog_has_expected_active_sources():
    active_keys = {item["key"] for item in OFFICIAL_SOURCE_CATALOG if item["ingest_status"] == "active"}
    assert {"kap", "borsa_istanbul", "bist_datastore", "tcmb", "tuik", "hmb", "mkk", "takasbank"}.issubset(active_keys)


async def test_source_catalog_endpoint_summary_counts():
    payload = await get_source_catalog()

    assert payload["summary"]["total"] == len(OFFICIAL_SOURCE_CATALOG)
    assert payload["summary"]["active"] == sum(1 for item in OFFICIAL_SOURCE_CATALOG if item["ingest_status"] == "active")
    assert payload["summary"]["scheduler_or_manual"] == sum(
        1 for item in OFFICIAL_SOURCE_CATALOG if item["scan_mode"] == "scheduler+manual"
    )
    assert payload["summary"]["on_demand"] == sum(
        1 for item in OFFICIAL_SOURCE_CATALOG if item["scan_mode"] == "on_demand"
    )


async def test_source_catalog_exposes_runner_availability():
    payload = await get_source_catalog()
    sources = {item["key"]: item for item in payload["sources"]}

    assert sources["kap"]["runner_available"] is True
    assert sources["borsa_istanbul"]["runner_available"] is True
    assert sources["bist_datastore"]["runner_available"] is True
    assert sources["hmb"]["runner_available"] is True
    assert sources["mkk"]["runner_available"] is True
    assert sources["takasbank"]["runner_available"] is True
    assert sources["tefas"]["runner_available"] is False
    assert sources["hmb"]["scan_mode"] == "scheduler+manual"
    assert sources["tefas"]["scan_mode"] == "on_demand"
    assert sources["borsa_istanbul"]["scan_mode"] == "scheduler+manual"
    assert sources["bist_datastore"]["scan_mode"] == "scheduler+manual"
    assert sources["mkk"]["scan_mode"] == "scheduler+manual"
    assert sources["takasbank"]["scan_mode"] == "scheduler+manual"
    assert sources["hmb"]["health_status"] in {"missing", "fresh", "failing"}
    assert sources["tefas"]["health_status"] == "not_run"
    assert sources["borsa_istanbul"]["health_status"] in {"missing", "fresh"}
    assert sources["bist_datastore"]["health_status"] in {"missing", "fresh"}
    assert sources["mkk"]["health_status"] in {"missing", "fresh"}
    assert sources["takasbank"]["health_status"] in {"missing", "fresh"}


async def test_source_catalog_summary_exposes_health_counts(monkeypatch):
    now = datetime.now(timezone.utc).isoformat()
    monkeypatch.setattr(
        admin,
        "get_all_source_health",
        lambda: {
            "kap": {
                "last_successful_fetch": now,
                "last_attempt_at": now,
            },
            "mkk": {
                "last_attempt_at": now,
                "last_error": "upstream timeout",
            },
        },
    )
    monkeypatch.setattr(admin, "get_source_health_ledger_snapshot", lambda source_keys=None, per_source_limit=5: {})

    payload = await get_source_catalog()

    assert payload["summary"]["health"]["fresh"] >= 1
    assert payload["summary"]["health"]["failing"] >= 1
    assert payload["summary"]["needs_attention"] >= 1


async def test_source_catalog_merges_ledger_attention_fields(monkeypatch):
    monkeypatch.setattr(
        admin,
        "get_all_source_health",
        lambda: {
            "kap": {
                "last_successful_fetch": "2026-04-24T03:00:00+00:00",
                "last_attempt_at": "2026-04-24T03:00:00+00:00",
            },
        },
    )
    monkeypatch.setattr(
        admin,
        "get_source_health_ledger_snapshot",
        lambda source_keys=None, per_source_limit=5: {
            "kap": {
                "last_outcome": "failure",
                "consecutive_failures": 2,
                "success_rate": 50.0,
                "recent_outcomes": ["success", "failure", "failure"],
                "history_size": 3,
                "trend": "deteriorating",
                "latest_recorded_at": "2026-04-24T03:05:00+00:00",
                "latest_error": "rss parse error",
                "recent_runs": [
                    {
                        "id": 1,
                        "status": "failure",
                        "error": "rss parse error",
                        "detail": {},
                        "recorded_at": "2026-04-24T03:05:00+00:00",
                    }
                ],
            }
        },
    )

    payload = await get_source_catalog()
    kap = next(item for item in payload["sources"] if item["key"] == "kap")

    assert kap["health_detail"]["trend"] == "deteriorating"
    assert kap["health_detail"]["alert_level"] == "warning"
    assert kap["health_detail"]["attention_required"] is True
    assert "yeniden tarama gerekli" in kap["health_detail"]["attention_reason"]


@pytest.mark.asyncio
async def test_source_health_history_endpoint_filters_and_caps_limit(monkeypatch):
    monkeypatch.setattr(
        admin,
        "get_source_health_history",
        lambda source_key=None, limit=20: [
            {
                "id": 8,
                "source_key": source_key or "kap",
                "status": "success",
                "error": None,
                "detail": {"stored_count": 5},
                "recorded_at": "2026-04-24T03:00:00+00:00",
            }
        ],
    )

    payload = await get_source_health_history_endpoint(source_key="kap", limit=500)

    assert payload["source_key"] == "kap"
    assert payload["limit"] == 100
    assert payload["count"] == 1
    assert payload["items"][0]["source_key"] == "kap"


@pytest.mark.asyncio
async def test_source_health_history_endpoint_rejects_unknown_source():
    with pytest.raises(HTTPException) as exc:
        await get_source_health_history_endpoint(source_key="unknown", limit=10)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_source_health_dashboard_aggregates_alerts_and_rollups(monkeypatch):
    now = datetime.now(timezone.utc).isoformat()
    monkeypatch.setattr(
        admin,
        "get_all_source_health",
        lambda: {
            "kap": {
                "last_attempt_at": now,
                "last_successful_fetch": now,
                "history": [{"status": "success"}],
            },
            "mkk": {
                "last_attempt_at": now,
                "last_error": "timeout",
                "history": [{"status": "failure"}, {"status": "failure"}],
            },
        },
    )
    monkeypatch.setattr(
        admin,
        "get_source_health_history",
        lambda source_key=None, limit=20: [
            {
                "id": 5,
                "source_key": "mkk",
                "status": "failure",
                "error": "timeout",
                "detail": {"attempt": 2},
                "recorded_at": "2026-04-24T04:00:00+00:00",
            },
            {
                "id": 4,
                "source_key": "mkk",
                "status": "failure",
                "error": "timeout",
                "detail": {"attempt": 1},
                "recorded_at": "2026-04-24T03:45:00+00:00",
            },
            {
                "id": 3,
                "source_key": "kap",
                "status": "success",
                "error": None,
                "detail": {"stored_count": 4},
                "recorded_at": "2026-04-24T03:00:00+00:00",
            },
        ],
    )
    monkeypatch.setattr(
        admin,
        "get_source_health_ledger_snapshot",
        lambda source_keys=None, per_source_limit=5: {
            "kap": {
                "recent_runs": [
                    {
                        "id": 3,
                        "status": "success",
                        "error": None,
                        "detail": {"stored_count": 4},
                        "recorded_at": "2026-04-24T03:00:00+00:00",
                    }
                ],
                "last_outcome": "success",
                "consecutive_failures": 0,
                "success_rate": 100.0,
                "recent_outcomes": ["success"],
                "history_size": 1,
                "trend": "stable",
                "latest_recorded_at": "2026-04-24T03:00:00+00:00",
                "latest_error": None,
            },
            "mkk": {
                "recent_runs": [
                    {
                        "id": 5,
                        "status": "failure",
                        "error": "timeout",
                        "detail": {"attempt": 2},
                        "recorded_at": "2026-04-24T04:00:00+00:00",
                    },
                    {
                        "id": 4,
                        "status": "failure",
                        "error": "timeout",
                        "detail": {"attempt": 1},
                        "recorded_at": "2026-04-24T03:45:00+00:00",
                    },
                ],
                "last_outcome": "failure",
                "consecutive_failures": 2,
                "success_rate": 0.0,
                "recent_outcomes": ["failure", "failure"],
                "history_size": 2,
                "trend": "deteriorating",
                "latest_recorded_at": "2026-04-24T04:00:00+00:00",
                "latest_error": "timeout",
            },
        },
    )

    payload = await get_source_health_dashboard(limit=40)

    assert payload["ledger"]["total_events"] == 3
    assert payload["ledger"]["failure_count"] == 2
    assert payload["ledger"]["failure_rate"] == 66.7
    assert payload["counts"]["at_risk_sources"] >= 1
    assert payload["metrics"]["open_incidents"] >= 1
    assert payload["metrics"]["max_failure_streak"] == 2
    assert payload["metrics"]["average_success_rate"] == 50.0
    assert any(item["title"].startswith("MKK") for item in payload["alerts"])
    assert payload["unstable_sources"][0]["source"]["key"] == "mkk"
    assert payload["recovery_candidates"] == []
    assert any(item["source"]["key"] == "kap" for item in payload["healthy_sources"])


@pytest.mark.asyncio
async def test_source_health_dashboard_surfaces_recovering_sources(monkeypatch):
    now = datetime.now(timezone.utc).isoformat()
    monkeypatch.setattr(
        admin,
        "get_all_source_health",
        lambda: {
            "tcmb": {
                "last_attempt_at": now,
                "last_successful_fetch": now,
                "history": [{"status": "failure"}, {"status": "success"}],
            },
        },
    )
    monkeypatch.setattr(
        admin,
        "get_source_health_history",
        lambda source_key=None, limit=20: [
            {
                "id": 8,
                "source_key": "tcmb",
                "status": "success",
                "error": None,
                "detail": {"stored_count": 2},
                "recorded_at": "2026-04-24T05:00:00+00:00",
            }
        ],
    )
    monkeypatch.setattr(
        admin,
        "get_source_health_ledger_snapshot",
        lambda source_keys=None, per_source_limit=5: {
            "tcmb": {
                "recent_runs": [
                    {
                        "id": 8,
                        "status": "success",
                        "error": None,
                        "detail": {"stored_count": 2},
                        "recorded_at": "2026-04-24T05:00:00+00:00",
                    },
                    {
                        "id": 7,
                        "status": "failure",
                        "error": "upstream timeout",
                        "detail": {},
                        "recorded_at": "2026-04-24T04:30:00+00:00",
                    },
                ],
                "last_outcome": "success",
                "consecutive_failures": 0,
                "success_rate": 50.0,
                "recent_outcomes": ["failure", "success"],
                "history_size": 2,
                "trend": "improving",
                "latest_recorded_at": "2026-04-24T05:00:00+00:00",
                "latest_error": None,
            },
        },
    )

    payload = await get_source_health_dashboard(limit=20)

    assert payload["metrics"]["recovering_sources"] >= 1
    assert payload["recovery_candidates"][0]["source"]["key"] == "tcmb"
    assert payload["recovery_candidates"][0]["incident_state"] == "recovering"


def test_is_source_active_matches_catalog():
    assert is_source_active("kap") is True
    assert is_source_active("borsa_istanbul") is True
    assert is_source_active("bist_datastore") is True
    assert is_source_active("hmb") is True
    assert is_source_active("mkk") is True
    assert is_source_active("takasbank") is True
    assert is_source_active("tefas") is False


@pytest.mark.asyncio
async def test_trigger_source_scan_rejects_unknown_source():
    with pytest.raises(HTTPException) as exc:
        await trigger_source_scan("unknown_source")

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_trigger_source_scan_runs_hmb_registry_runner(monkeypatch):
    from app.services import official_news_ingest

    async def fake_run() -> int:
        return 3

    monkeypatch.setattr(official_news_ingest, "run_hmb_scan", fake_run)

    payload = await trigger_source_scan("hmb")

    assert payload["status"] == "completed"
    assert payload["source_key"] == "hmb"
    assert payload["stored"] == 3


@pytest.mark.asyncio
async def test_trigger_source_scan_runs_mkk_registry_runner(monkeypatch):
    from app.services import official_news_ingest

    async def fake_run() -> int:
        return 7

    monkeypatch.setattr(official_news_ingest, "run_mkk_scan", fake_run)

    payload = await trigger_source_scan("mkk")

    assert payload["status"] == "completed"
    assert payload["source_key"] == "mkk"
    assert payload["stored"] == 7


@pytest.mark.asyncio
async def test_bist_datastore_endpoint_records_success(monkeypatch):
    captured = {}

    async def fake_fetch(limit: int = 20, category_code: str = "PPB"):
        assert limit == 4
        assert category_code == "PPB"
        return [
            {
                "title": "Piyasa Değerleri",
                "market": "Pay Piyasası Verileri",
                "market_key": "pay_piyasasi",
                "update_frequency": "Güncel",
                "source": "Borsa İstanbul Veri Store",
                "catalog_url": "https://www.borsaistanbul.com/veriler/konsolide-veriler",
                "datastore_url": "https://datastore.borsaistanbul.com",
            }
        ]

    monkeypatch.setattr(
        admin,
        "record_source_success",
        lambda source, detail=None: captured.update({"source": source, "detail": detail}),
    )
    monkeypatch.setattr(bist_datastore_adapter, "fetch_dataset_catalog", fake_fetch)

    payload = await get_bist_datastore_catalog(limit=4)

    assert payload["count"] == 1
    assert payload["datasets"][0]["market_key"] == "pay_piyasasi"
    assert captured["source"] == "bist_datastore"
    assert captured["detail"]["returned_count"] == 1


@pytest.mark.asyncio
async def test_bist_datastore_product_files_endpoint_records_success(monkeypatch):
    captured = {}

    async def fake_fetch(product_type_id: str, page: int = 1, page_size: int = 20):
        assert product_type_id == "3157"
        assert page == 1
        assert page_size == 5
        return {
            "product_type_id": "3157",
            "count": 1,
            "page": 1,
            "page_size": 5,
            "items": [
                {
                    "id": 6584561,
                    "file_name": "PP_AYLIKOZET.M.202603.zip",
                    "download_endpoint": "https://datastore.borsaistanbul.com/api/file/6584561",
                }
            ],
        }

    monkeypatch.setattr(
        admin,
        "record_source_success",
        lambda source, detail=None: captured.update({"source": source, "detail": detail}),
    )
    monkeypatch.setattr(bist_datastore_adapter, "fetch_product_files", fake_fetch)

    payload = await get_bist_datastore_product_files(product_type_id="3157", page_size=5)

    assert payload["count"] == 1
    assert payload["items"][0]["id"] == 6584561
    assert captured["source"] == "bist_datastore"
    assert captured["detail"]["product_type_id"] == "3157"


@pytest.mark.asyncio
async def test_bist_datastore_latest_snapshot_endpoint(monkeypatch):
    from app.services import bist_datastore_archive

    async def fake_fetch(category_code=None, product_type_id=None, limit=100):
        assert category_code == "PPB"
        assert product_type_id == "3157"
        assert limit == 25
        return {
            "snapshot_date": "2026-04-25",
            "count": 1,
            "items": [
                {
                    "dataset_title": "Kapanış Fiyatları",
                    "product_type_id": "3157",
                    "file_id": "6584561",
                    "file_name": "PP_AYLIKOZET.M.202603.zip",
                }
            ],
        }

    monkeypatch.setattr(bist_datastore_archive, "get_latest_bist_datastore_snapshot", fake_fetch)

    payload = await get_bist_datastore_latest_snapshot(category_code="PPB", product_type_id="3157", limit=25)

    assert payload["snapshot_date"] == "2026-04-25"
    assert payload["count"] == 1
    assert payload["items"][0]["file_id"] == "6584561"


@pytest.mark.asyncio
async def test_bist_datastore_backfill_endpoint(monkeypatch):
    from app.services import bist_datastore_archive

    async def fake_backfill(category_code="PPB", dataset_limit=20, files_per_dataset=5):
        assert category_code == "PPB"
        assert dataset_limit == 12
        assert files_per_dataset == 4
        return {
            "snapshot_date": "2026-04-25",
            "category_code": "PPB",
            "dataset_count": 2,
            "stored_count": 6,
            "items": [],
        }

    monkeypatch.setattr(bist_datastore_archive, "persist_bist_datastore_snapshot", fake_backfill)

    payload = await backfill_bist_datastore_snapshot(category_code="PPB", dataset_limit=12, files_per_dataset=4)

    assert payload["snapshot_date"] == "2026-04-25"
    assert payload["dataset_count"] == 2
    assert payload["stored_count"] == 6


@pytest.mark.asyncio
async def test_bist_datastore_archive_latest_endpoint(monkeypatch):
    from app.services import bist_datastore_file_archive

    async def fake_archive(category_code="PPB", product_type_id=None, limit=5, overwrite=False):
        assert category_code == "PPB"
        assert product_type_id == "3157"
        assert limit == 2
        assert overwrite is True
        return {
            "snapshot_date": "2026-04-25",
            "count": 2,
            "downloaded_count": 2,
            "skipped_count": 0,
            "items": [{"file_name": "PP_AYLIKOZET.M.202603.zip"}],
        }

    monkeypatch.setattr(bist_datastore_file_archive, "archive_latest_bist_datastore_files", fake_archive)

    payload = await archive_bist_datastore_latest_files(
        category_code="PPB",
        product_type_id="3157",
        limit=2,
        overwrite=True,
    )

    assert payload["snapshot_date"] == "2026-04-25"
    assert payload["downloaded_count"] == 2
    assert payload["items"][0]["file_name"] == "PP_AYLIKOZET.M.202603.zip"


@pytest.mark.asyncio
async def test_bist_datastore_archive_listing_endpoint(monkeypatch):
    from app.services import bist_datastore_file_archive

    async def fake_list(snapshot_date=None, limit=20):
        assert snapshot_date == "2026-04-25"
        assert limit == 10
        return {
            "snapshot_date": "2026-04-25",
            "count": 1,
            "items": [{"archive_path": "/tmp/archive.zip", "file_name": "archive.zip"}],
        }

    monkeypatch.setattr(bist_datastore_file_archive, "list_archived_bist_datastore_files", fake_list)

    payload = await get_bist_datastore_archive(snapshot_date="2026-04-25", limit=10)

    assert payload["snapshot_date"] == "2026-04-25"
    assert payload["count"] == 1
    assert payload["items"][0]["file_name"] == "archive.zip"


@pytest.mark.asyncio
async def test_tefas_endpoint_records_success(monkeypatch):
    captured = {}

    async def fake_fetch(_fund_code: str):
        return {
            "fund_code": "AFT",
            "fund_name": "Ak Portfoy Teknoloji",
        }

    monkeypatch.setattr(admin, "record_source_success", lambda source, detail=None: captured.update({"source": source, "detail": detail}))
    monkeypatch.setattr(tefas_adapter, "fetch_fund_detail", fake_fetch)

    payload = await get_tefas_fund_detail("aft")

    assert payload["fund"]["fund_code"] == "AFT"
    assert captured["source"] == "tefas"
    assert captured["detail"]["fund_code"] == "AFT"


@pytest.mark.asyncio
async def test_tefas_universe_endpoint_records_success(monkeypatch):
    captured = {}

    async def fake_fetch(fund_type: str, limit: int):
        assert limit == 50
        assert fund_type == "YAT"
        return {
            "fund_type": "YAT",
            "fund_type_label": "Menkul Kıymet Yatırım Fonları",
            "total": 2,
            "count": 1,
            "items": [{"fund_code": "AFT", "fund_name": "Ak Portfoy", "source": "TEFAS"}],
        }

    monkeypatch.setattr(admin, "record_source_success", lambda source, detail=None: captured.update({"source": source, "detail": detail}))
    monkeypatch.setattr(tefas_adapter, "fetch_fund_universe", fake_fetch)

    payload = await get_tefas_universe(fund_type="YAT", limit=50)

    assert payload["fund_type"] == "YAT"
    assert payload["count"] == 1
    assert payload["items"][0]["fund_code"] == "AFT"
    assert captured["source"] == "tefas"
    assert captured["detail"]["fund_type"] == "YAT"


@pytest.mark.asyncio
async def test_borsa_endpoint_records_failure_when_empty(monkeypatch):
    captured = {}

    async def fake_fetch(limit: int = 10):
        assert limit == 3
        return []

    monkeypatch.setattr(
        admin,
        "record_source_failure",
        lambda source, error, detail=None: captured.update({"source": source, "error": error, "detail": detail}),
    )
    monkeypatch.setattr(borsa_announcements_adapter, "fetch_latest_announcements", fake_fetch)

    payload = await get_borsa_istanbul_announcements(limit=3)

    assert payload["count"] == 0
    assert captured["source"] == "borsa_istanbul"
    assert captured["detail"]["limit"] == 3


@pytest.mark.asyncio
async def test_hmb_endpoint_records_success(monkeypatch):
    captured = {}

    async def fake_fetch(limit: int = 10):
        assert limit == 2
        return [
            {
                "title": "Mart 2026 Merkezi Yonetim Butce Gerceklesmeleri",
                "category": "butce",
                "published_on": "15.04.2026",
                "url": "https://www.hmb.gov.tr/example.pdf",
                "source": "HMB",
            }
        ]

    monkeypatch.setattr(
        admin,
        "record_source_success",
        lambda source, detail=None: captured.update({"source": source, "detail": detail}),
    )
    monkeypatch.setattr(hmb_adapter, "fetch_latest_publications", fake_fetch)

    payload = await get_hmb_publications(limit=2)

    assert payload["count"] == 1
    assert payload["publications"][0]["source"] == "HMB"
    assert captured["source"] == "hmb"
    assert captured["detail"]["returned_count"] == 1


@pytest.mark.asyncio
async def test_health_check_includes_official_ingest_sources_without_degrading(monkeypatch):
    now = datetime.now(timezone.utc)

    class FakeScalarResult:
        def __init__(self, value):
            self.value = value

        def scalar(self):
            return self.value

        def scalar_one_or_none(self):
            return self.value

    class FakeSession:
        def __init__(self):
            self.values = iter(
                [
                    100,
                    now,
                    now,
                    now,
                    now,
                        now,
                        now,
                        now,
                        now,
                        0,
                        4,
                        2,
                    0,
                    0,
                    2,
                    1,
                    now,
                    0,
                    0,
                ]
            )

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def execute(self, _query):
            return FakeScalarResult(next(self.values))

    monkeypatch.setattr(
        admin,
        "get_all_source_health",
        lambda: {
            "borsa_istanbul": {
                "last_attempt_at": "2026-04-24T03:00:00+00:00",
                "last_successful_fetch": "2026-04-24T03:00:00+00:00",
                "detail": {"returned_count": 4},
            },
            "hmb": {
                "last_attempt_at": "2026-04-24T03:00:00+00:00",
                "last_successful_fetch": "2026-04-24T03:00:00+00:00",
                "detail": {"returned_count": 2},
            }
        },
    )
    monkeypatch.setattr(
        admin,
        "get_source_health_ledger_snapshot",
        lambda source_keys=None, per_source_limit=5: {},
    )

    payload = await health_check(db=FakeSession())

    assert payload["status"] == "healthy"
    assert "borsa_istanbul" in payload["sources"]
    assert "hmb" in payload["sources"]
    assert payload["sources"]["borsa_istanbul"]["status"] == "fresh"
    assert payload["sources"]["hmb"]["status"] == "fresh"
    assert payload["sources"]["borsa_istanbul"]["records"] == 4
    assert payload["sources"]["hmb"]["records"] == 2
    assert payload["sources"]["mkk"]["records"] == 2
    assert payload["sources"]["takasbank"]["records"] == 1
    assert payload["sources"]["borsa_istanbul"]["last_outcome"] == "success"
    assert payload["sources"]["borsa_istanbul"]["success_rate"] == 100.0
    assert payload["sources"]["borsa_istanbul"]["recent_outcomes"] == ["success"]
