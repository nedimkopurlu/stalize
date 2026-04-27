"""Resmi kaynak ingest registry.

Aktif resmi kaynak taramalarını tek merkezden tetiklemek için kullanılır.
"""

from __future__ import annotations

from typing import Awaitable, Callable, Dict

from app.data.official_sources import get_official_source_map
from app.services.source_health import record_source_failure, record_source_success


SourceRunner = Callable[[], Awaitable[int]]


async def _run_kap() -> int:
    from app.services.kap_parser import run_kap_scan

    return await run_kap_scan()


async def _run_tcmb() -> int:
    from app.services.tcmb_adapter import run_tcmb_scan

    return await run_tcmb_scan()


async def _run_tuik() -> int:
    from app.services.tuik_adapter import run_tuik_scan

    return await run_tuik_scan()


async def _run_borsa_istanbul() -> int:
    from app.services.official_news_ingest import run_borsa_istanbul_scan

    return await run_borsa_istanbul_scan()


async def _run_bist_datastore() -> int:
    from app.services.bist_datastore_archive import persist_bist_datastore_snapshot

    payload = await persist_bist_datastore_snapshot(category_code="PPB", dataset_limit=20, files_per_dataset=5)
    return int(payload.get("stored_count") or 0)


async def _run_mkk() -> int:
    from app.services.official_news_ingest import run_mkk_scan

    return await run_mkk_scan()


async def _run_hmb() -> int:
    from app.services.official_news_ingest import run_hmb_scan

    return await run_hmb_scan()


async def _run_takasbank() -> int:
    from app.services.official_news_ingest import run_takasbank_scan

    return await run_takasbank_scan()


async def _run_tefas() -> int:
    from app.services.tefas_adapter import tefas_adapter
    from app.services.tefas_snapshot import persist_tefas_universe_snapshot

    universe = await tefas_adapter.fetch_all_fund_universes(limit_per_type=100)
    total = int(universe.get("count") or 0)
    stored = 0
    if total > 0:
        stored = await persist_tefas_universe_snapshot(universe)
        record_source_success(
            "tefas",
            detail={"returned_count": total, "stored_count": stored, "type_count": universe.get("type_count")},
        )
    else:
        record_source_failure(
            "tefas",
            "No funds returned from TEFAS universe",
            detail={"type_count": universe.get("type_count")},
        )
    return stored


ACTIVE_SOURCE_RUNNERS: Dict[str, SourceRunner] = {
    "kap": _run_kap,
    "borsa_istanbul": _run_borsa_istanbul,
    "bist_datastore": _run_bist_datastore,
    "tcmb": _run_tcmb,
    "tuik": _run_tuik,
    "hmb": _run_hmb,
    "mkk": _run_mkk,
    "takasbank": _run_takasbank,
    "tefas": _run_tefas,
}


def get_source_runner(source_key: str) -> SourceRunner | None:
    return ACTIVE_SOURCE_RUNNERS.get(source_key)


def is_source_active(source_key: str) -> bool:
    source = get_official_source_map().get(source_key)
    return bool(source and source["ingest_status"] == "active" and source_key in ACTIVE_SOURCE_RUNNERS)
