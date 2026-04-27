"""Official source announcement ingestion helpers.

Persists Borsa Istanbul, MKK and Takasbank records into NewsItem so
official-source scans are no longer runtime-only.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Optional, Sequence

from sqlalchemy import or_, select

from app.core.database import AsyncSessionLocal
from app.models.news import NewsItem
from app.services.bist_datastore_adapter import bist_datastore_adapter
from app.services.borsa_announcements import borsa_announcements_adapter
from app.services.hmb_adapter import hmb_adapter
from app.services.mkk_adapter import mkk_adapter
from app.services.source_health import record_source_failure, record_source_success
from app.services.takasbank_adapter import takasbank_adapter


logger = logging.getLogger(__name__)

_TR_MONTHS = {
    "ocak": 1,
    "oca": 1,
    "subat": 2,
    "şubat": 2,
    "sub": 2,
    "şub": 2,
    "mart": 3,
    "mar": 3,
    "nisan": 4,
    "nis": 4,
    "mayis": 5,
    "mayıs": 5,
    "may": 5,
    "haziran": 6,
    "haz": 6,
    "temmuz": 7,
    "tem": 7,
    "agustos": 8,
    "ağustos": 8,
    "agu": 8,
    "ağu": 8,
    "eylul": 9,
    "eylül": 9,
    "eyl": 9,
    "ekim": 10,
    "eki": 10,
    "kasim": 11,
    "kasım": 11,
    "kas": 11,
    "aralik": 12,
    "aralık": 12,
    "ara": 12,
}


def _parse_tr_date(value: Optional[str], default_year: Optional[int] = None) -> Optional[datetime]:
    if not value:
        return None

    parts = value.strip().split()
    if len(parts) not in {2, 3}:
        return None

    try:
        day = int(parts[0])
    except ValueError:
        return None

    month = _TR_MONTHS.get(parts[1].strip().lower())
    if month is None:
        return None

    year = default_year
    if len(parts) == 3:
        try:
            year = int(parts[2])
        except ValueError:
            return None

    if year is None:
        year = datetime.now(timezone.utc).year

    try:
        return datetime(year, month, day, tzinfo=timezone.utc)
    except ValueError:
        return None


def _record_timestamp(item: dict[str, Any], default_year: Optional[int] = None) -> datetime:
    published_on = item.get("published_on")
    if isinstance(published_on, str):
        parsed = _parse_tr_date(published_on)
        if parsed is not None:
            return parsed

    period = item.get("period")
    if isinstance(period, str):
        parsed = _parse_tr_date(f"1 {period}", default_year=default_year)
        if parsed is not None:
            return parsed

    return datetime.now(timezone.utc)


async def _store_items(
    *,
    source_key: str,
    source_name: str,
    category: str,
    items: Sequence[dict[str, Any]],
    title_getter: Callable[[dict[str, Any]], str],
    summary_getter: Callable[[dict[str, Any]], Optional[str]],
) -> int:
    if not items:
        record_source_failure(source_key, "No records returned from official source", detail={"stored_count": 0})
        return 0

    stored = 0
    fetched = len(items)

    try:
        async with AsyncSessionLocal() as db:
            for item in items:
                title = title_getter(item).strip()
                url = str(item.get("url") or "").strip()
                if not title:
                    continue

                duplicate_clause = NewsItem.title == title
                if url:
                    duplicate_clause = or_(NewsItem.url == url, NewsItem.title == title)

                existing = await db.execute(
                    select(NewsItem).where(
                        NewsItem.source == source_name,
                        duplicate_clause,
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                db.add(
                    NewsItem(
                        stock_id=None,
                        title=title,
                        summary=summary_getter(item),
                        url=url or None,
                        source=source_name,
                        language="tr",
                        category=category,
                        published_at=_record_timestamp(item),
                        sentiment_score=0.0,
                        sentiment_label="neutral",
                        sentiment_confidence=0.6,
                        importance_score=0.6,
                        is_processed=False,
                    )
                )
                stored += 1

            await db.commit()
    except Exception as exc:
        logger.error("%s ingest commit hatası: %s", source_name, exc)
        record_source_failure(source_key, str(exc), detail={"fetched_count": fetched, "stored_count": stored})
        return 0

    if stored > 0:
        record_source_success(source_key, detail={"fetched_count": fetched, "stored_count": stored})
    else:
        record_source_failure(source_key, "No new records persisted", detail={"fetched_count": fetched, "stored_count": 0})

    return stored


async def run_borsa_istanbul_scan(limit: int = 25) -> int:
    announcements = await borsa_announcements_adapter.fetch_latest_announcements(limit=limit)
    return await _store_items(
        source_key="borsa_istanbul",
        source_name="Borsa İstanbul",
        category="exchange",
        items=announcements,
        title_getter=lambda item: str(item.get("headline") or ""),
        summary_getter=lambda item: f"Resmi duyuru tarihi: {item['published_on']}" if item.get("published_on") else None,
    )


async def run_mkk_scan(limit: int = 12) -> int:
    bulletins = await mkk_adapter.fetch_latest_bulletins(limit=limit)
    return await _store_items(
        source_key="mkk",
        source_name="MKK",
        category="custody",
        items=bulletins,
        title_getter=lambda item: str(item.get("title") or ""),
        summary_getter=lambda item: f"Resmi piyasa bülteni dönemi: {item['period']}" if item.get("period") else None,
    )


async def run_takasbank_scan(limit: int = 20) -> int:
    announcements = await takasbank_adapter.fetch_latest_announcements(limit=limit)
    return await _store_items(
        source_key="takasbank",
        source_name="Takasbank",
        category="settlement",
        items=announcements,
        title_getter=lambda item: str(item.get("headline") or ""),
        summary_getter=lambda item: item.get("category"),
    )


async def run_hmb_scan(limit: int = 12) -> int:
    publications = await hmb_adapter.fetch_latest_publications(limit=limit)
    return await _store_items(
        source_key="hmb",
        source_name="HMB",
        category="fiscal",
        items=publications,
        title_getter=lambda item: str(item.get("title") or ""),
        summary_getter=lambda item: (
            f"Resmi HMB yayını ({item.get('category')})"
            if item.get("category")
            else "Resmi HMB yayını"
        ),
    )


async def run_bist_datastore_scan(limit: int = 20) -> int:
    datasets = await bist_datastore_adapter.fetch_dataset_catalog(limit=limit)
    if not datasets:
        record_source_failure(
            "bist_datastore",
            "No datasets returned from public datastore catalog",
            detail={"limit": limit},
        )
        return 0

    record_source_success(
        "bist_datastore",
        detail={
            "limit": limit,
            "returned_count": len(datasets),
            "markets": sorted({str(item.get("market_key")) for item in datasets if item.get("market_key")}),
        },
    )
    return len(datasets)
