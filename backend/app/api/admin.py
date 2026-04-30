from __future__ import annotations

"""Admin domain router — sağlık kontrolü, manuel tarama tetikleyicileri, dashboard."""
import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_api_key
from app.data.official_sources import OFFICIAL_SOURCE_CATALOG, get_official_source_map
from app.models.stock import Stock
from app.models.news import NewsItem
from app.models.portfolio_v2 import PortfolioDailySnapshot
from app.models.bist_datastore import BistDatastoreFileSnapshot
from app.services.official_ingest import get_source_runner, is_source_active
from app.services.scoring import scoring_engine
from app.services.source_health import (
    get_all_source_health,
    get_source_health_ledger_snapshot,
    get_source_health_history,
    record_source_failure,
    record_source_success,
    summarize_source_runtime,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _age_status(last_seen: Optional[datetime], warn_after_hours: int) -> Dict:
    if last_seen is None:
        return {
            "status": "missing",
            "last_seen": None,
            "age_minutes": None,
        }

    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    age_minutes = round((now - last_seen).total_seconds() / 60, 1)
    status = "fresh" if age_minutes <= warn_after_hours * 60 else "stale"

    return {
        "status": status,
        "last_seen": last_seen.isoformat(),
        "age_minutes": age_minutes,
    }


def _parse_runtime_ts(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def _source_warn_after_hours(source_key: str) -> int:
    source = get_official_source_map().get(source_key)
    if source and str(source.get("warn_after_hours") or "").isdigit():
        return int(str(source["warn_after_hours"]))

    warn_after_hours = {
        "portfolio_snapshot": 48,
    }
    return warn_after_hours.get(source_key, 168)


def _apply_attention_signal(
    payload: Dict[str, Any],
    *,
    source_key: str,
    ingest_status: str,
    scan_mode: str,
    status_note: Optional[str] = None,
) -> Dict[str, Any]:
    enriched = {
        **payload,
        "freshness_policy": {
            "warn_after_hours": _source_warn_after_hours(source_key),
            "cadence": (
                get_official_source_map().get(source_key, {}).get("cadence")
                or ("manual_only" if scan_mode == "on_demand" else "scheduled")
            ),
        },
    }
    enriched.update(
        _build_attention_signal(
            ingest_status=ingest_status,
            scan_mode=scan_mode,
            health_status=enriched["status"],
            detail=enriched,
            status_note=status_note,
        )
    )
    return enriched


def _build_runtime_only_source_health(source_key: str, runtime: Dict[str, Any], scan_mode: str) -> Dict[str, Any]:
    success_at = _parse_runtime_ts(runtime.get("last_successful_fetch"))
    attempt_at = _parse_runtime_ts(runtime.get("last_attempt_at"))
    warn_after_hours = _source_warn_after_hours(source_key)
    runtime_summary = summarize_source_runtime(runtime)

    if success_at:
        payload = _age_status(success_at, warn_after_hours=warn_after_hours)
    elif attempt_at and runtime.get("last_error"):
        now = datetime.now(timezone.utc)
        payload = {
            "status": "failing",
            "last_seen": None,
            "age_minutes": round((now - attempt_at).total_seconds() / 60, 1),
        }
    elif scan_mode == "on_demand":
        payload = {
            "status": "not_run",
            "last_seen": None,
            "age_minutes": None,
        }
    else:
        payload = {
            "status": "missing",
            "last_seen": None,
            "age_minutes": None,
        }

    return {
        **payload,
        "last_successful_fetch": runtime.get("last_successful_fetch"),
        "last_attempt_at": runtime.get("last_attempt_at"),
        "last_error": runtime.get("last_error"),
        "last_error_at": runtime.get("last_error_at"),
        "detail": runtime.get("detail", {}),
        **runtime_summary,
        "records": None,
    }


def _merge_health_summaries(
    health_payload: Dict[str, Any],
    ledger_summary: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    if not ledger_summary:
        return health_payload

    return {
        **health_payload,
        "last_outcome": ledger_summary.get("last_outcome", health_payload.get("last_outcome")),
        "consecutive_failures": ledger_summary.get("consecutive_failures", health_payload.get("consecutive_failures")),
        "success_rate": ledger_summary.get("success_rate", health_payload.get("success_rate")),
        "recent_outcomes": ledger_summary.get("recent_outcomes", health_payload.get("recent_outcomes")),
        "history_size": ledger_summary.get("history_size", health_payload.get("history_size")),
        "trend": ledger_summary.get("trend", health_payload.get("trend")),
        "latest_ledger_at": ledger_summary.get("latest_recorded_at"),
        "latest_ledger_error": ledger_summary.get("latest_error"),
        "ledger_event_count": len(ledger_summary.get("recent_runs", [])),
    }


def _build_attention_signal(
    *,
    ingest_status: str,
    scan_mode: str,
    health_status: str,
    detail: Dict[str, Any],
    status_note: Optional[str] = None,
) -> Dict[str, Any]:
    trend = detail.get("trend")
    consecutive_failures = detail.get("consecutive_failures") or 0

    if ingest_status == "planned":
        return {
            "alert_level": "planned",
            "attention_required": True,
            "attention_reason": status_note or "Kaynak henüz yol haritasında bekliyor.",
        }

    if health_status == "failing":
        return {
            "alert_level": "critical",
            "attention_required": True,
            "attention_reason": detail.get("last_error") or "Son kaynak koşusu başarısız oldu.",
        }

    if health_status == "missing" and scan_mode == "scheduler+manual":
        return {
            "alert_level": "warning",
            "attention_required": True,
            "attention_reason": "Beklenen scheduler/manual akışında henüz kalıcı veri oluşmadı.",
        }

    if health_status == "stale":
        return {
            "alert_level": "warning",
            "attention_required": True,
            "attention_reason": "Kaynak tazelik eşiğini aştı; yeniden tarama gerekli.",
        }

    if consecutive_failures >= 2:
        return {
            "alert_level": "watch",
            "attention_required": True,
            "attention_reason": f"Son koşularda {consecutive_failures} ardışık hata görüldü.",
        }

    if health_status == "not_run":
        return {
            "alert_level": "watch",
            "attention_required": False,
            "attention_reason": "On-demand kaynak henüz tetiklenmedi.",
        }

    if trend == "deteriorating":
        return {
            "alert_level": "watch",
            "attention_required": True,
            "attention_reason": "Son koşu paterni bozuluyor; yakından izlenmeli.",
        }

    return {
        "alert_level": "ok",
        "attention_required": False,
        "attention_reason": None,
    }


def _build_catalog_source_item(
    item: Dict[str, str],
    source_runtime: Dict[str, Any],
    ledger_snapshot: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    runtime = {} if item["ingest_status"] == "planned" else source_runtime.get(item["key"], {})
    health_payload = _build_runtime_only_source_health(
        item["key"],
        runtime,
        item["scan_mode"],
    )
    health_payload = _merge_health_summaries(health_payload, ledger_snapshot.get(item["key"]))
    health_payload = _apply_attention_signal(
        health_payload,
        source_key=item["key"],
        ingest_status=item["ingest_status"],
        scan_mode=item["scan_mode"],
        status_note=item.get("status_note"),
    )
    return {
        **item,
        "runner_available": is_source_active(item["key"]),
        "health": runtime,
        "health_status": health_payload["status"],
        "health_detail": health_payload,
    }


def _get_source_catalog_payload() -> Dict[str, Any]:
    source_runtime = get_all_source_health()
    ledger_snapshot = get_source_health_ledger_snapshot(
        source_keys=[item["key"] for item in OFFICIAL_SOURCE_CATALOG],
        per_source_limit=5,
    )
    sources = [
        _build_catalog_source_item(item, source_runtime, ledger_snapshot)
        for item in OFFICIAL_SOURCE_CATALOG
    ]

    health_summary = {
        "fresh": sum(1 for item in sources if item["health_status"] == "fresh"),
        "failing": sum(1 for item in sources if item["health_status"] == "failing"),
        "stale": sum(1 for item in sources if item["health_status"] == "stale"),
        "missing": sum(1 for item in sources if item["health_status"] == "missing"),
        "not_run": sum(1 for item in sources if item["health_status"] == "not_run"),
    }

    return {
        "sources": sources,
        "summary": {
            "total": len(OFFICIAL_SOURCE_CATALOG),
            "active": sum(1 for item in OFFICIAL_SOURCE_CATALOG if item["ingest_status"] == "active"),
            "planned": sum(1 for item in OFFICIAL_SOURCE_CATALOG if item["ingest_status"] == "planned"),
            "scheduler_or_manual": sum(
                1 for item in OFFICIAL_SOURCE_CATALOG if item["scan_mode"] == "scheduler+manual"
            ),
            "on_demand": sum(1 for item in OFFICIAL_SOURCE_CATALOG if item["scan_mode"] == "on_demand"),
            "needs_attention": sum(1 for item in sources if item["health_detail"].get("attention_required")),
            "health": health_summary,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _build_source_health_dashboard_payload(limit: int = 40) -> Dict[str, Any]:
    catalog_payload = _get_source_catalog_payload()
    sources = catalog_payload["sources"]
    history = get_source_health_history(limit=limit)
    ledger_snapshot = get_source_health_ledger_snapshot(
        source_keys=[source["key"] for source in sources],
        per_source_limit=5,
    )
    recent_events = history[:12]
    total_events = len(history)
    failure_count = sum(1 for item in history if item["status"] == "failure")
    success_count = sum(1 for item in history if item["status"] == "success")
    failure_rate = round((failure_count / total_events) * 100, 1) if total_events else None

    def build_rollup(source: Dict[str, Any]) -> Dict[str, Any]:
        source_history = ledger_snapshot.get(source["key"], {}).get("recent_runs", [])
        source_failure_count = sum(1 for item in source_history if item["status"] == "failure")
        source_success_count = sum(1 for item in source_history if item["status"] == "success")
        latest_event = source_history[0] if source_history else None
        success_ratio = round((source_success_count / len(source_history)) * 100, 1) if source_history else None
        trend = source["health_detail"].get("trend")
        last_outcome = source["health_detail"].get("last_outcome")
        consecutive_failures = source["health_detail"].get("consecutive_failures") or 0
        attention_required = bool(source["health_detail"].get("attention_required"))
        alert_level = source["health_detail"].get("alert_level")
        risk_score = (
            source_failure_count * 10
            + (consecutive_failures * 6)
            + (12 if source["health_status"] == "failing" else 0)
            + (9 if source["health_status"] == "missing" else 0)
            + (5 if source["health_status"] == "stale" else 0)
            + (4 if trend == "deteriorating" else 0)
        )
        freshness_rank = (
            (0 if source["health_status"] == "fresh" else 20)
            + (consecutive_failures * 10)
            + (source_failure_count * 4)
            - source_success_count
        )
        if source["ingest_status"] == "planned":
            incident_state = "planned"
        elif trend == "improving" and last_outcome == "success":
            incident_state = "recovering"
        elif attention_required and alert_level in {"critical", "warning"}:
            incident_state = "open"
        elif attention_required or alert_level == "watch":
            incident_state = "watch"
        else:
            incident_state = "stable"
        return {
            "source": source,
            "history": source_history,
            "failure_count": source_failure_count,
            "success_count": source_success_count,
            "latest_event": latest_event,
            "risk_score": risk_score,
            "success_ratio": success_ratio,
            "freshness_rank": freshness_rank,
            "incident_state": incident_state,
        }

    source_rollups = [build_rollup(source) for source in sources]
    unstable_sources = [
        item
        for item in source_rollups
        if item["history"] or item["source"]["health_status"] != "fresh"
    ]
    unstable_sources.sort(key=lambda item: item["risk_score"], reverse=True)

    healthy_sources = [
        item
        for item in source_rollups
        if item["source"]["health_status"] == "fresh" or item["success_count"] > 0
    ]
    healthy_sources.sort(key=lambda item: item["freshness_rank"])
    recovery_candidates = [item for item in source_rollups if item["incident_state"] == "recovering"]
    recovery_candidates.sort(key=lambda item: item["freshness_rank"])

    success_rates = [
        item["success_ratio"]
        for item in source_rollups
        if item["success_ratio"] is not None and item["source"]["ingest_status"] == "active"
    ]
    open_incidents = sum(1 for item in source_rollups if item["incident_state"] == "open")
    watchlist_sources = sum(1 for item in source_rollups if item["incident_state"] == "watch")
    recovering_sources = len(recovery_candidates)
    max_failure_streak = max(
        ((item["source"]["health_detail"].get("consecutive_failures") or 0) for item in source_rollups),
        default=0,
    )
    average_success_rate = round(sum(success_rates) / len(success_rates), 1) if success_rates else None

    alerts = [
        {
            "id": f"{source['key']}-{source['health_status']}",
            "severity": (
                "critical"
                if source["health_detail"].get("alert_level") == "critical"
                else "high"
                if source["health_detail"].get("alert_level") == "warning"
                else "medium"
                if source["health_detail"].get("alert_level") == "watch"
                else "planned"
            ),
            "title": (
                f"{source['name']} hata modunda"
                if source["health_detail"].get("alert_level") == "critical"
                else f"{source['name']} dikkat istiyor"
                if source["health_detail"].get("alert_level") in {"warning", "watch"}
                else f"{source['name']} halen plan bekliyor"
            ),
            "detail": source["health_detail"].get("attention_reason")
            or source["status_note"]
            or "Operasyonel takip gerekiyor.",
            "note": (
                f"Son deneme {datetime.fromisoformat(source['health_detail']['last_attempt_at']).astimezone(timezone.utc).isoformat()}"
                if source["health_detail"].get("last_attempt_at")
                else source["scan_mode"]
            ),
            "score": _source_warn_after_hours(source["key"]) + (0 if source["priority"] == "tier1" else 1000),
        }
        for source in sources
        if source["health_detail"].get("attention_required") or source["ingest_status"] == "planned"
    ]

    if failure_rate is not None and total_events >= 8 and failure_rate >= 35:
        alerts.append(
            {
                "id": "ledger-failure-rate",
                "severity": "high",
                "title": "Ledger hata oranı yükseldi",
                "detail": f"Son {total_events} olayın {failure_count} tanesi başarısız.",
                "note": f"Başarı oranı %{max(0.0, 100 - failure_rate):.1f}",
                "score": -1,
            }
        )

    severity_rank = {"critical": 0, "high": 1, "medium": 2, "planned": 3}
    alerts.sort(key=lambda item: (severity_rank.get(item["severity"], 9), item["score"]))

    return {
        "source_catalog": catalog_payload,
        "ledger": {
            "total_events": total_events,
            "success_count": success_count,
            "failure_count": failure_count,
            "failure_rate": failure_rate,
            "recent_events": recent_events,
        },
        "counts": {
            "at_risk_sources": sum(1 for source in sources if source["health_status"] in {"failing", "missing", "stale"}),
            "planned_sources": sum(1 for source in sources if source["ingest_status"] == "planned"),
        },
        "metrics": {
            "open_incidents": open_incidents,
            "watchlist_sources": watchlist_sources,
            "recovering_sources": recovering_sources,
            "max_failure_streak": max_failure_streak,
            "average_success_rate": average_success_rate,
        },
        "alerts": alerts[:6],
        "unstable_sources": unstable_sources[:6],
        "recovery_candidates": recovery_candidates[:4],
        "healthy_sources": healthy_sources[:5],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Sağlık kontrolü + veri tazeliği özeti."""
    source_runtime = get_all_source_health()
    ledger_snapshot = get_source_health_ledger_snapshot(
        source_keys=[
            item["key"]
            for item in OFFICIAL_SOURCE_CATALOG
            if item["ingest_status"] == "active"
        ] + ["portfolio_snapshot"],
        per_source_limit=5,
    )

    stock_count = (
        await db.execute(select(func.count(Stock.id)).where(Stock.is_active))
    ).scalar() or 0

    kap_last = (
        await db.execute(
            select(func.max(NewsItem.created_at)).where(NewsItem.source == "KAP")
        )
    ).scalar_one_or_none()
    borsa_last = (
        await db.execute(
            select(func.max(NewsItem.created_at)).where(NewsItem.source == "Borsa İstanbul")
        )
    ).scalar_one_or_none()
    hmb_last = (
        await db.execute(
            select(func.max(NewsItem.created_at)).where(NewsItem.source == "HMB")
        )
    ).scalar_one_or_none()
    tcmb_last = (
        await db.execute(
            select(func.max(NewsItem.created_at)).where(NewsItem.source == "TCMB")
        )
    ).scalar_one_or_none()
    tuik_last = (
        await db.execute(
            select(func.max(NewsItem.created_at)).where(NewsItem.source == "TUIK")
        )
    ).scalar_one_or_none()
    mkk_last = (
        await db.execute(
            select(func.max(NewsItem.created_at)).where(NewsItem.source == "MKK")
        )
    ).scalar_one_or_none()
    takasbank_last = (
        await db.execute(
            select(func.max(NewsItem.created_at)).where(NewsItem.source == "Takasbank")
        )
    ).scalar_one_or_none()
    snapshot_last = (
        await db.execute(select(func.max(PortfolioDailySnapshot.created_at)))
    ).scalar_one_or_none()

    kap_count = (
        await db.execute(select(func.count(NewsItem.id)).where(NewsItem.source == "KAP"))
    ).scalar() or 0
    borsa_count = (
        await db.execute(select(func.count(NewsItem.id)).where(NewsItem.source == "Borsa İstanbul"))
    ).scalar() or 0
    hmb_count = (
        await db.execute(select(func.count(NewsItem.id)).where(NewsItem.source == "HMB"))
    ).scalar() or 0
    tcmb_count = (
        await db.execute(select(func.count(NewsItem.id)).where(NewsItem.source == "TCMB"))
    ).scalar() or 0
    tuik_count = (
        await db.execute(select(func.count(NewsItem.id)).where(NewsItem.source == "TUIK"))
    ).scalar() or 0
    mkk_count = (
        await db.execute(select(func.count(NewsItem.id)).where(NewsItem.source == "MKK"))
    ).scalar() or 0
    takasbank_count = (
        await db.execute(select(func.count(NewsItem.id)).where(NewsItem.source == "Takasbank"))
    ).scalar() or 0
    bist_datastore_last = (
        await db.execute(select(func.max(BistDatastoreFileSnapshot.created_at)))
    ).scalar()
    bist_datastore_count = (
        await db.execute(select(func.count(BistDatastoreFileSnapshot.id)))
    ).scalar() or 0
    snapshot_count = (
        await db.execute(select(func.count(PortfolioDailySnapshot.id)))
    ).scalar() or 0

    def with_runtime(source_key: str, payload: Dict) -> Dict:
        runtime = source_runtime.get(source_key, {})
        runtime_summary = summarize_source_runtime(runtime)
        merged = {
            **payload,
            "last_successful_fetch": runtime.get("last_successful_fetch"),
            "last_attempt_at": runtime.get("last_attempt_at"),
            "last_error": runtime.get("last_error"),
            "last_error_at": runtime.get("last_error_at"),
            "detail": runtime.get("detail", {}),
            **runtime_summary,
        }
        merged = _merge_health_summaries(merged, ledger_snapshot.get(source_key))
        success_at = _parse_runtime_ts(runtime.get("last_successful_fetch"))
        if success_at and merged["status"] == "missing":
            merged.update(_age_status(success_at, warn_after_hours=24))
        merged = _apply_attention_signal(
            merged,
            source_key=source_key,
            ingest_status="active",
            scan_mode="scheduler+manual",
        )
        return merged

    db_backed_sources = {
        "kap": (kap_last, kap_count),
        "borsa_istanbul": (borsa_last, borsa_count),
        "hmb": (hmb_last, hmb_count),
        "tcmb": (tcmb_last, tcmb_count),
        "tuik": (tuik_last, tuik_count),
        "mkk": (mkk_last, mkk_count),
        "takasbank": (takasbank_last, takasbank_count),
        "bist_datastore": (bist_datastore_last, bist_datastore_count),
    }
    sources: Dict[str, Dict[str, Any]] = {}

    for item in OFFICIAL_SOURCE_CATALOG:
        if item["ingest_status"] != "active":
            continue

        source_key = item["key"]
        if source_key in db_backed_sources:
            last_seen, record_count = db_backed_sources[source_key]
            payload = with_runtime(
                source_key,
                _age_status(last_seen, warn_after_hours=_source_warn_after_hours(source_key)),
            )
            payload["records"] = record_count
        else:
            payload = _build_runtime_only_source_health(
                source_key,
                source_runtime.get(source_key, {}),
                item["scan_mode"],
            )
            payload = _merge_health_summaries(payload, ledger_snapshot.get(source_key))
            payload = _apply_attention_signal(
                payload,
                source_key=source_key,
                ingest_status=item["ingest_status"],
                scan_mode=item["scan_mode"],
                status_note=item.get("status_note"),
            )

        sources[source_key] = payload

    sources["portfolio_snapshot"] = {
        **with_runtime(
            "portfolio_snapshot",
            _age_status(snapshot_last, warn_after_hours=_source_warn_after_hours("portfolio_snapshot")),
        ),
        "records": snapshot_count,
    }

    for source_key, source in list(sources.items()):
        if source.get("status") != "stale" or not source.get("last_successful_fetch"):
            continue
        success_at = _parse_runtime_ts(source["last_successful_fetch"])
        if success_at:
            source.update(_age_status(success_at, warn_after_hours=_source_warn_after_hours(source_key)))
            sources[source_key] = _apply_attention_signal(
                source,
                source_key=source_key,
                ingest_status="active",
                scan_mode="scheduler+manual",
            )

    if sources["portfolio_snapshot"].get("detail", {}).get("reason") == "no_active_positions":
        sources["portfolio_snapshot"]["status"] = "idle"
        sources["portfolio_snapshot"]["alert_level"] = "ok"
        sources["portfolio_snapshot"]["attention_required"] = False
        sources["portfolio_snapshot"]["attention_reason"] = "Aktif pozisyon olmadığı için snapshot beklemede."

    overall_status = "healthy"
    blocking_sources = {"kap", "tcmb", "tuik"}
    if any(
        source_key in blocking_sources and source["status"] in {"missing", "failing"}
        for source_key, source in sources.items()
    ):
        overall_status = "degraded"
    if sources["kap"]["status"] == "stale":
        overall_status = "degraded"

    canonical_symbols = settings.BIST100_SYMBOLS

    return {
        "status": overall_status,
        "stocks_in_db": stock_count,
        "canonical_universe_count": len(canonical_symbols),
        "universe_sync": stock_count == len(canonical_symbols),
        "universe_scope": "BIST100",
        "official_source_count": len(OFFICIAL_SOURCE_CATALOG),
        "active_official_source_count": sum(1 for item in OFFICIAL_SOURCE_CATALOG if item["ingest_status"] == "active"),
        "sources": sources,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/sources/catalog")
async def get_source_catalog():
    """Resmi kaynak omurgasının kapsama durumunu getir."""
    return _get_source_catalog_payload()


@router.get("/sources/health/dashboard")
async def get_source_health_dashboard(limit: int = 40):
    """Source health görünümünü dashboard için toplu üret."""
    return _build_source_health_dashboard_payload(limit=max(1, min(limit, 100)))


@router.get("/sources/health/history")
async def get_source_health_history_endpoint(source_key: Optional[str] = None, limit: int = 20):
    """Source health ledger geçmişini getir."""
    if source_key and source_key not in {*get_official_source_map().keys(), "portfolio_snapshot"}:
        raise HTTPException(status_code=404, detail=f"Bilinmeyen kaynak: {source_key}")

    items = get_source_health_history(source_key=source_key, limit=limit)
    return {
        "items": items,
        "source_key": source_key,
        "limit": max(1, min(limit, 100)),
        "count": len(items),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/sources/scan/{source_key}")
async def trigger_source_scan(source_key: str, _: None = Depends(verify_api_key)):
    """Aktif resmi kaynaklardan birini generic ingest registry üzerinden tetikle."""
    source = get_official_source_map().get(source_key)
    if not source:
        raise HTTPException(status_code=404, detail=f"Bilinmeyen kaynak: {source_key}")

    runner = get_source_runner(source_key)
    if runner is None:
        raise HTTPException(
            status_code=409,
            detail=f"{source['name']} için ingest hazır değil: {source['status_note']}",
        )

    stored = await runner()
    return {
        "status": "completed",
        "source": source["name"],
        "source_key": source_key,
        "stored": stored,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/sources/tefas/fund/{fund_code}")
async def get_tefas_fund_detail(fund_code: str):
    """TEFAS fon detayını resmi sayfadan on-demand getir."""
    from app.services.tefas_adapter import tefas_adapter

    detail = await tefas_adapter.fetch_fund_detail(fund_code)
    if detail is None:
        record_source_failure(
            "tefas",
            f"Fund not found or unreadable: {fund_code.upper()}",
            detail={"fund_code": fund_code.upper()},
        )
        raise HTTPException(status_code=404, detail=f"TEFAS fonu bulunamadı veya okunamadı: {fund_code.upper()}")

    record_source_success(
        "tefas",
        detail={"fund_code": detail["fund_code"], "fund_name": detail["fund_name"]},
    )
    return {
        "source": "TEFAS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fund": detail,
    }


@router.get("/sources/tefas/universe")
async def get_tefas_universe(fund_type: str = "ALL", limit: int = 100):
    """TEFAS fon evrenini resmi karşılaştırma servisinden getir."""
    from app.services.tefas_adapter import tefas_adapter

    fund_type = fund_type.strip().upper()
    if fund_type == "ALL":
        payload = await tefas_adapter.fetch_all_fund_universes(limit_per_type=limit)
        total = int(payload.get("count") or 0)
        if total > 0:
            record_source_success(
                "tefas",
                detail={"returned_count": total, "type_count": payload.get("type_count")},
            )
        else:
            record_source_failure("tefas", "No funds returned from TEFAS universe", detail={"fund_type": "ALL"})

        return {
            "source": "TEFAS",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **payload,
        }

    payload = await tefas_adapter.fetch_fund_universe(fund_type=fund_type, limit=limit)
    if payload["count"] > 0:
        record_source_success(
            "tefas",
            detail={"fund_type": fund_type, "returned_count": payload["count"], "total": payload["total"]},
        )
    else:
        record_source_failure("tefas", "No funds returned from TEFAS universe", detail={"fund_type": fund_type})

    return {
        "source": "TEFAS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **payload,
    }


@router.get("/sources/tefas/snapshots/latest")
async def get_tefas_latest_snapshot(
    fund_type: Optional[str] = None,
    limit: int = 100,
    auto_refresh: bool = True,
):
    """Kalıcı TEFAS snapshot katmanındaki son evren görüntüsünü getir."""
    from app.services.tefas_snapshot import ensure_fresh_tefas_snapshot, get_latest_tefas_snapshot, tefas_snapshot_is_stale

    if auto_refresh:
        payload = await ensure_fresh_tefas_snapshot(fund_type=fund_type, limit=limit)
    else:
        payload = await get_latest_tefas_snapshot(fund_type=fund_type, limit=limit)
        payload = {
            **payload,
            "auto_refresh_attempted": False,
            "auto_refresh_performed": False,
            "is_stale": tefas_snapshot_is_stale(payload.get("snapshot_date")),
        }
    return {
        "source": "TEFAS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **payload,
    }


@router.get("/sources/borsa-istanbul/announcements")
async def get_borsa_istanbul_announcements(limit: int = 10):
    """Borsa İstanbul resmi duyurularını on-demand getir."""
    from app.services.borsa_announcements import borsa_announcements_adapter

    announcements = await borsa_announcements_adapter.fetch_latest_announcements(limit=limit)
    if announcements:
        record_source_success(
            "borsa_istanbul",
            detail={"limit": limit, "returned_count": len(announcements)},
        )
    else:
        record_source_failure(
            "borsa_istanbul",
            "No announcements returned from official source",
            detail={"limit": limit},
        )
    return {
        "source": "Borsa İstanbul",
        "count": len(announcements),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "announcements": announcements,
    }


@router.get("/sources/bist-datastore/catalog")
async def get_bist_datastore_catalog(limit: int = 20, category_code: str = "PPB"):
    """Borsa İstanbul Veri Store dataset kataloğunu on-demand getir."""
    from app.services.bist_datastore_adapter import bist_datastore_adapter

    datasets = await bist_datastore_adapter.fetch_dataset_catalog(limit=limit, category_code=category_code)
    if datasets:
        record_source_success(
            "bist_datastore",
            detail={
                "limit": limit,
                "category_code": category_code.upper(),
                "returned_count": len(datasets),
                "markets": sorted({item["market_key"] for item in datasets}),
            },
        )
    else:
        record_source_failure(
            "bist_datastore",
            "No datasets returned from public datastore catalog",
            detail={"limit": limit, "category_code": category_code.upper()},
        )

    return {
        "source": "Borsa İstanbul Veri Store",
        "count": len(datasets),
        "category_code": category_code.upper(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "datasets": datasets,
    }


@router.get("/sources/bist-datastore/product-type/{product_type_id}/files")
async def get_bist_datastore_product_files(
    product_type_id: str,
    page: int = 1,
    page_size: int = 20,
    probe_download: bool = False,
):
    """Veri Store ürün tipi için son dosya listesini getir."""
    from app.services.bist_datastore_adapter import bist_datastore_adapter

    payload = await bist_datastore_adapter.fetch_product_files(
        product_type_id=product_type_id,
        page=max(page, 1),
        page_size=max(1, min(page_size, 100)),
    )
    if probe_download:
        enriched_items = []
        for item in payload["items"]:
            probe = await bist_datastore_adapter.probe_file_download(str(item["id"]))
            enriched_items.append({**item, "download_probe": probe})
        payload["items"] = enriched_items

    if payload["count"] > 0:
        record_source_success(
            "bist_datastore",
            detail={
                "product_type_id": product_type_id,
                "returned_count": payload["count"],
                "page": payload["page"],
                "page_size": payload["page_size"],
                "probe_download": probe_download,
            },
        )
    else:
        record_source_failure(
            "bist_datastore",
            "No product files returned from public datastore endpoint",
            detail={
                "product_type_id": product_type_id,
                "page": payload["page"],
                "page_size": payload["page_size"],
                "probe_download": probe_download,
            },
        )

    return {
        "source": "Borsa İstanbul Veri Store",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **payload,
    }


@router.get("/sources/bist-datastore/snapshots/latest")
async def get_bist_datastore_latest_snapshot(
    category_code: Optional[str] = None,
    product_type_id: Optional[str] = None,
    limit: int = 100,
):
    """Kalıcı Veri Store dosya snapshot katmanındaki son görüntüyü getir."""
    from app.services.bist_datastore_archive import get_latest_bist_datastore_snapshot

    payload = await get_latest_bist_datastore_snapshot(
        category_code=category_code,
        product_type_id=product_type_id,
        limit=limit,
    )
    return {
        "source": "Borsa İstanbul Veri Store",
        "category_code": category_code.strip().upper() if category_code else None,
        "product_type_id": product_type_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **payload,
    }


@router.post("/sources/bist-datastore/backfill")
async def backfill_bist_datastore_snapshot(
    category_code: str = "PPB",
    dataset_limit: int = 20,
    files_per_dataset: int = 5,
    _: None = Depends(verify_api_key),
):
    """Veri Store dosya metadata katmanını kalıcı snapshot olarak doldur."""
    from app.services.bist_datastore_archive import persist_bist_datastore_snapshot

    payload = await persist_bist_datastore_snapshot(
        category_code=category_code,
        dataset_limit=dataset_limit,
        files_per_dataset=files_per_dataset,
    )
    return {
        "source": "Borsa İstanbul Veri Store",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **payload,
    }


@router.post("/sources/bist-datastore/archive/latest")
async def archive_bist_datastore_latest_files(
    category_code: str = "PPB",
    product_type_id: Optional[str] = None,
    limit: int = 5,
    overwrite: bool = False,
    _: None = Depends(verify_api_key),
):
    """Son Veri Store snapshot'indaki dosyalari runtime arsivine indir."""
    from app.services.bist_datastore_file_archive import archive_latest_bist_datastore_files

    payload = await archive_latest_bist_datastore_files(
        category_code=category_code,
        product_type_id=product_type_id,
        limit=limit,
        overwrite=overwrite,
    )
    return {
        "source": "Borsa İstanbul Veri Store",
        "category_code": category_code.strip().upper(),
        "product_type_id": product_type_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **payload,
    }


@router.get("/sources/bist-datastore/archive")
async def get_bist_datastore_archive(snapshot_date: Optional[str] = None, limit: int = 20):
    """Runtime'a indirilen Veri Store dosyalarini listele."""
    from app.services.bist_datastore_file_archive import list_archived_bist_datastore_files

    payload = await list_archived_bist_datastore_files(snapshot_date=snapshot_date, limit=limit)
    return {
        "source": "Borsa İstanbul Veri Store",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **payload,
    }


@router.get("/sources/mkk/monthly-bulletins")
async def get_mkk_monthly_bulletins(limit: int = 10):
    """MKK aylık piyasa bültenlerini resmi kaynaktan on-demand getir."""
    from app.services.mkk_adapter import mkk_adapter

    bulletins = await mkk_adapter.fetch_latest_bulletins(limit=limit)
    if bulletins:
        record_source_success(
            "mkk",
            detail={"limit": limit, "returned_count": len(bulletins)},
        )
    else:
        record_source_failure(
            "mkk",
            "No bulletins returned from official source",
            detail={"limit": limit},
        )
    return {
        "source": "MKK",
        "count": len(bulletins),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "bulletins": bulletins,
    }


@router.get("/sources/hmb/publications")
async def get_hmb_publications(limit: int = 10):
    """HMB butce ve borclanma odakli resmi yayinlarini on-demand getir."""
    from app.services.hmb_adapter import hmb_adapter

    publications = await hmb_adapter.fetch_latest_publications(limit=limit)
    if publications:
        record_source_success(
            "hmb",
            detail={"limit": limit, "returned_count": len(publications)},
        )
    else:
        record_source_failure(
            "hmb",
            "No publications returned from official source",
            detail={"limit": limit},
        )
    return {
        "source": "HMB",
        "count": len(publications),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "publications": publications,
    }


@router.get("/sources/takasbank/announcements")
async def get_takasbank_announcements(limit: int = 10):
    """Takasbank resmi duyurularını on-demand getir."""
    from app.services.takasbank_adapter import takasbank_adapter

    announcements = await takasbank_adapter.fetch_latest_announcements(limit=limit)
    if announcements:
        record_source_success(
            "takasbank",
            detail={"limit": limit, "returned_count": len(announcements)},
        )
    else:
        record_source_failure(
            "takasbank",
            "No announcements returned from official source",
            detail={"limit": limit},
        )
    return {
        "source": "Takasbank",
        "count": len(announcements),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "announcements": announcements,
    }


@router.post("/kap/scan")
async def trigger_kap_scan(_: None = Depends(verify_api_key)):
    """KAP taramasını manuel tetikle."""
    from app.services.kap_parser import run_kap_scan

    stored = await run_kap_scan()
    return {
        "status": "completed",
        "stored": stored,
        "source": "KAP",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/dashboard")
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Ana dashboard verileri — hızlı özet."""
    # Top 5 Alım & Top 5 Satım
    top_buy_result = await db.execute(
        select(Stock)
        .where(and_(Stock.is_active, Stock.overall_score.isnot(None)))
        .order_by(Stock.overall_score.desc())
        .limit(5)
    )
    top_buy = top_buy_result.scalars().all()

    top_sell_result = await db.execute(
        select(Stock)
        .where(and_(Stock.is_active, Stock.overall_score.isnot(None)))
        .order_by(Stock.overall_score.asc())
        .limit(5)
    )
    top_sell = top_sell_result.scalars().all()

    # En çok yükselen / düşen (günlük)
    top_gainer_result = await db.execute(
        select(Stock)
        .where(and_(Stock.is_active, Stock.daily_change_pct.isnot(None)))
        .order_by(Stock.daily_change_pct.desc())
        .limit(5)
    )
    top_gainers = top_gainer_result.scalars().all()

    top_loser_result = await db.execute(
        select(Stock)
        .where(and_(Stock.is_active, Stock.daily_change_pct.isnot(None)))
        .order_by(Stock.daily_change_pct.asc())
        .limit(5)
    )
    top_losers = top_loser_result.scalars().all()

    # İstatistikler
    stats_result = await db.execute(
        select(
            func.count(Stock.id),
            func.avg(Stock.overall_score),
            func.count().filter(Stock.recommendation == "GÜÇLÜ AL"),
            func.count().filter(Stock.recommendation == "AL"),
            func.count().filter(Stock.recommendation == "TUT"),
            func.count().filter(Stock.recommendation == "SAT"),
            func.count().filter(Stock.recommendation == "GÜÇLÜ SAT"),
        ).where(Stock.is_active)
    )
    stats = stats_result.fetchone()

    def stock_to_dict(s):
        return {
            "symbol": s.symbol, "name": s.name, "sector": s.sector,
            "current_price": s.current_price, "daily_change_pct": s.daily_change_pct,
            "volume": s.volume, "market_cap": s.market_cap,
            "overall_score": s.overall_score, "recommendation": s.recommendation,
            "is_bist30": s.is_bist30,
            "technical_score": s.technical_score,
            "fundamental_score": s.fundamental_score,
            "sentiment_score": s.sentiment_score,
        }

    return {
        "top_buy": [stock_to_dict(s) for s in top_buy],
        "top_sell": [stock_to_dict(s) for s in top_sell],
        "top_gainers": [stock_to_dict(s) for s in top_gainers],
        "top_losers": [stock_to_dict(s) for s in top_losers],
        "stats": {
            "total_stocks": stats[0] if stats else 0,
            "avg_score": round(float(stats[1]), 2) if stats and stats[1] else None,
            "strong_buy_count": stats[2] if stats else 0,
            "buy_count": stats[3] if stats else 0,
            "hold_count": stats[4] if stats else 0,
            "sell_count": stats[5] if stats else 0,
            "strong_sell_count": stats[6] if stats else 0,
        },
    }
