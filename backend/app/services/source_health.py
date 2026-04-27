"""Kaynak bazlı sağlık ve hata durumu kaydı.

Gerçek veri toplayıcılarının son başarılı çekimini ve son hata nedenini
repo içindeki kalıcı JSON runtime dosyasında tutar; ek olarak deneme
geçmişini sorgulanabilir bir DB ledger tablosuna yazar.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import sync_engine
from app.models.source_health import SourceHealthRun


RUNTIME_DIR = Path(__file__).resolve().parents[2] / "runtime"
STATE_FILE = RUNTIME_DIR / "source_health.json"
STATE_LOCK = RLock()
HISTORY_LIMIT = 12
LEDGER_LIMIT_MAX = 100
LEDGER_PER_SOURCE_LIMIT_MAX = 20

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_state() -> Dict[str, Any]:
    if not STATE_FILE.exists():
        return {}

    try:
        raw_state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

    if not isinstance(raw_state, dict):
        return {}

    normalized: Dict[str, Any] = {}
    for source, payload in raw_state.items():
        if not isinstance(payload, dict):
            continue
        history = payload.get("history")
        normalized[source] = {
            **payload,
            "history": history if isinstance(history, list) else [],
        }
    return normalized


def _write_state(state: Dict[str, Any]) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = STATE_FILE.with_suffix(".tmp")
    tmp_path.write_text(
        json.dumps(state, ensure_ascii=True, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    tmp_path.replace(STATE_FILE)


def _append_history_event(previous: Dict[str, Any], event: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    history = previous.get("history")
    if not isinstance(history, list):
        history = []
    if event is None:
        return history[-HISTORY_LIMIT:]
    return [*history[-(HISTORY_LIMIT - 1):], event]


def _update_state(source: str, payload: Dict[str, Any], history_event: Optional[Dict[str, Any]] = None) -> None:
    with STATE_LOCK:
        state = _read_state()
        previous = state.get(source, {})
        state[source] = {
            **previous,
            **payload,
            "history": _append_history_event(previous, history_event),
        }
        _write_state(state)


def _persist_ledger_event(
    source: str,
    status: str,
    *,
    error: Optional[str] = None,
    detail: Optional[Dict[str, Any]] = None,
) -> None:
    try:
        with Session(sync_engine) as session:
            session.add(
                SourceHealthRun(
                    source_key=source,
                    status=status,
                    error=error[:500] if error else None,
                    detail=detail,
                )
            )
            session.commit()
    except SQLAlchemyError as exc:
        logger.warning("source health ledger write skipped: %s", exc)


def record_source_success(source: str, detail: Optional[Dict[str, Any]] = None) -> None:
    now = _utc_now()
    _update_state(
        source,
        {
            "last_attempt_at": now,
            "last_successful_fetch": now,
            "last_error": None,
            "last_error_at": None,
            "detail": detail or {},
        },
        history_event={
            "status": "success",
            "timestamp": now,
            "detail": detail or {},
        },
    )
    _persist_ledger_event(source, "success", detail=detail or {})


def record_source_failure(source: str, error: str, detail: Optional[Dict[str, Any]] = None) -> None:
    now = _utc_now()
    _update_state(
        source,
        {
            "last_attempt_at": now,
            "last_error": error[:500],
            "last_error_at": now,
            "detail": detail,
        } if detail is not None else {
            "last_attempt_at": now,
            "last_error": error[:500],
            "last_error_at": now,
        },
        history_event={
            "status": "failure",
            "timestamp": now,
            "error": error[:500],
            "detail": detail,
        },
    )
    _persist_ledger_event(source, "failure", error=error, detail=detail)


def summarize_source_runtime(runtime: Dict[str, Any]) -> Dict[str, Any]:
    history = runtime.get("history")
    if not isinstance(history, list):
        history = []

    if not history:
        inferred_status = None
        if runtime.get("last_error") and runtime.get("last_error_at"):
            inferred_status = "failure"
        elif runtime.get("last_successful_fetch"):
            inferred_status = "success"
        if inferred_status:
            history = [{"status": inferred_status}]

    outcomes = [
        item.get("status")
        for item in history
        if isinstance(item, dict) and item.get("status") in {"success", "failure"}
    ]
    return _summarize_outcomes(outcomes)


def _classify_trend(recent_outcomes: List[str]) -> str:
    if len(recent_outcomes) < 2:
        return "unknown"

    latest = recent_outcomes[-1]
    previous = recent_outcomes[-2]

    if latest == "success" and previous == "failure":
        return "improving"
    if latest == "failure" and previous == "success":
        return "deteriorating"

    last_three = recent_outcomes[-3:]
    if len(last_three) == 3 and all(item == "success" for item in last_three):
        return "stable"
    if last_three.count("failure") >= 2:
        return "deteriorating"

    return "stable"


def _summarize_outcomes(outcomes: List[str]) -> Dict[str, Any]:
    recent_outcomes = outcomes[-5:]
    consecutive_failures = 0
    for outcome in reversed(outcomes):
        if outcome != "failure":
            break
        consecutive_failures += 1

    success_count = sum(1 for outcome in outcomes if outcome == "success")
    success_rate = round((success_count / len(outcomes)) * 100, 1) if outcomes else None

    return {
        "last_outcome": recent_outcomes[-1] if recent_outcomes else None,
        "consecutive_failures": consecutive_failures,
        "success_rate": success_rate,
        "recent_outcomes": recent_outcomes,
        "history_size": len(outcomes),
        "trend": _classify_trend(recent_outcomes),
    }


def get_all_source_health() -> Dict[str, Any]:
    with STATE_LOCK:
        return _read_state()


def get_source_health_history(source_key: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    capped_limit = max(1, min(limit, LEDGER_LIMIT_MAX))

    try:
        with Session(sync_engine) as session:
            stmt = select(SourceHealthRun).order_by(
                SourceHealthRun.recorded_at.desc(),
                SourceHealthRun.id.desc(),
            )
            if source_key:
                stmt = stmt.where(SourceHealthRun.source_key == source_key)
            rows = session.execute(stmt.limit(capped_limit)).scalars().all()
    except SQLAlchemyError as exc:
        logger.warning("source health ledger read skipped: %s", exc)
        return []

    return [
        {
            "id": row.id,
            "source_key": row.source_key,
            "status": row.status,
            "error": row.error,
            "detail": row.detail or {},
            "recorded_at": row.recorded_at.isoformat() if row.recorded_at else None,
        }
        for row in rows
    ]


def get_source_health_ledger_snapshot(
    source_keys: List[str] | None = None,
    per_source_limit: int = 5,
) -> Dict[str, Dict[str, Any]]:
    capped_limit = max(1, min(per_source_limit, LEDGER_PER_SOURCE_LIMIT_MAX))

    try:
        with Session(sync_engine) as session:
            row_number = func.row_number().over(
                partition_by=SourceHealthRun.source_key,
                order_by=(SourceHealthRun.recorded_at.desc(), SourceHealthRun.id.desc()),
            ).label("rn")
            ranked_runs = select(
                SourceHealthRun.id.label("id"),
                SourceHealthRun.source_key.label("source_key"),
                SourceHealthRun.status.label("status"),
                SourceHealthRun.error.label("error"),
                SourceHealthRun.detail.label("detail"),
                SourceHealthRun.recorded_at.label("recorded_at"),
                row_number,
            )

            if source_keys:
                ranked_runs = ranked_runs.where(SourceHealthRun.source_key.in_(source_keys))

            ranked_subquery = ranked_runs.subquery()
            stmt = (
                select(ranked_subquery)
                .where(ranked_subquery.c.rn <= capped_limit)
                .order_by(
                    ranked_subquery.c.source_key.asc(),
                    ranked_subquery.c.recorded_at.desc(),
                    ranked_subquery.c.id.desc(),
                )
            )
            rows = session.execute(stmt).mappings().all()
    except SQLAlchemyError as exc:
        logger.warning("source health ledger snapshot skipped: %s", exc)
        return {}

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["source_key"], []).append(
            {
                "id": row["id"],
                "status": row["status"],
                "error": row["error"],
                "detail": row["detail"] or {},
                "recorded_at": row["recorded_at"].isoformat() if row["recorded_at"] else None,
            }
        )

    snapshot: Dict[str, Dict[str, Any]] = {}
    for source_key, items in grouped.items():
        latest = items[0]
        outcomes = [item["status"] for item in reversed(items) if item["status"] in {"success", "failure"}]
        summary = _summarize_outcomes(outcomes)
        snapshot[source_key] = {
            **summary,
            "latest_recorded_at": latest["recorded_at"],
            "latest_error": latest["error"],
            "recent_runs": items,
        }

    return snapshot
