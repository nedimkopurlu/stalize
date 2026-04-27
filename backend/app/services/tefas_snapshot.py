"""TEFAS evren snapshot persistence helpers."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal
from app.models.fund_snapshot import TefasFundSnapshot


async def persist_tefas_universe_snapshot(universe_payload: Dict[str, Any], snapshot_date: Optional[date] = None) -> int:
    snapshot_date = snapshot_date or date.today()
    fund_types = universe_payload.get("fund_types", []) or []
    rows: List[TefasFundSnapshot] = []

    for fund_type_payload in fund_types:
        fund_type = str(fund_type_payload.get("fund_type") or "")
        fund_type_label = str(fund_type_payload.get("fund_type_label") or fund_type)
        for item in fund_type_payload.get("items", []) or []:
            fund_code = str(item.get("fund_code") or "").strip().upper()
            fund_name = str(item.get("fund_name") or "").strip()
            if not fund_code or not fund_name:
                continue

            rows.append(
                TefasFundSnapshot(
                    snapshot_date=snapshot_date,
                    fund_code=fund_code,
                    fund_name=fund_name,
                    fund_type=fund_type,
                    fund_type_label=fund_type_label,
                    umbrella_type=item.get("umbrella_type"),
                    one_month_return_pct=item.get("one_month_return_pct"),
                    three_month_return_pct=item.get("three_month_return_pct"),
                    six_month_return_pct=item.get("six_month_return_pct"),
                    year_to_date_return_pct=item.get("year_to_date_return_pct"),
                    one_year_return_pct=item.get("one_year_return_pct"),
                    three_year_return_pct=item.get("three_year_return_pct"),
                    five_year_return_pct=item.get("five_year_return_pct"),
                    detail_url=item.get("detail_url"),
                )
            )

    async with AsyncSessionLocal() as db:
        await db.execute(delete(TefasFundSnapshot).where(TefasFundSnapshot.snapshot_date == snapshot_date))
        db.add_all(rows)
        await db.commit()

    return len(rows)


async def get_latest_tefas_snapshot_date() -> Optional[date]:
    async with AsyncSessionLocal() as db:
        return await db.scalar(
            select(TefasFundSnapshot.snapshot_date)
            .order_by(TefasFundSnapshot.snapshot_date.desc())
            .limit(1)
        )


async def get_latest_tefas_snapshot(fund_type: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    async with AsyncSessionLocal() as db:
        latest_date = await db.scalar(
            select(TefasFundSnapshot.snapshot_date)
            .order_by(TefasFundSnapshot.snapshot_date.desc())
            .limit(1)
        )
        if latest_date is None:
            return {"snapshot_date": None, "count": 0, "items": []}

        query = select(TefasFundSnapshot).where(TefasFundSnapshot.snapshot_date == latest_date)
        if fund_type:
            query = query.where(TefasFundSnapshot.fund_type == fund_type.upper())
        query = query.order_by(TefasFundSnapshot.fund_code.asc()).limit(limit)

        rows = (await db.execute(query)).scalars().all()

    items = [
        {
            "fund_code": row.fund_code,
            "fund_name": row.fund_name,
            "fund_type": row.fund_type,
            "fund_type_label": row.fund_type_label,
            "umbrella_type": row.umbrella_type,
            "one_month_return_pct": row.one_month_return_pct,
            "three_month_return_pct": row.three_month_return_pct,
            "six_month_return_pct": row.six_month_return_pct,
            "year_to_date_return_pct": row.year_to_date_return_pct,
            "one_year_return_pct": row.one_year_return_pct,
            "three_year_return_pct": row.three_year_return_pct,
            "five_year_return_pct": row.five_year_return_pct,
            "detail_url": row.detail_url,
        }
        for row in rows
    ]

    return {
        "snapshot_date": latest_date.isoformat(),
        "count": len(items),
        "items": items,
    }


def _get_tefas_runner():
    from app.services.official_ingest import get_source_runner

    return get_source_runner("tefas")


def _coerce_snapshot_date(snapshot_date: Optional[str]) -> Optional[date]:
    if not snapshot_date:
        return None
    try:
        return date.fromisoformat(snapshot_date)
    except ValueError:
        return None


def tefas_snapshot_is_stale(snapshot_date: Optional[str], max_age_days: int = 1) -> bool:
    parsed = _coerce_snapshot_date(snapshot_date)
    if parsed is None:
        return True
    age_days = (datetime.now(timezone.utc).date() - parsed).days
    return age_days > max_age_days


async def ensure_fresh_tefas_snapshot(
    *,
    fund_type: Optional[str] = None,
    limit: int = 100,
    max_age_days: int = 1,
) -> Dict[str, Any]:
    payload = await get_latest_tefas_snapshot(fund_type=fund_type, limit=limit)
    if not tefas_snapshot_is_stale(payload.get("snapshot_date"), max_age_days=max_age_days):
        return {
            **payload,
            "auto_refresh_attempted": False,
            "auto_refresh_performed": False,
            "is_stale": False,
        }

    runner = _get_tefas_runner()
    if runner is None:
        return {
            **payload,
            "auto_refresh_attempted": False,
            "auto_refresh_performed": False,
            "is_stale": True,
        }

    await runner()
    refreshed = await get_latest_tefas_snapshot(fund_type=fund_type, limit=limit)
    return {
        **refreshed,
        "auto_refresh_attempted": True,
        "auto_refresh_performed": True,
        "is_stale": tefas_snapshot_is_stale(refreshed.get("snapshot_date"), max_age_days=max_age_days),
    }
