"""Frontend'in kullandığı temel sistem ve dashboard endpoint'leri."""
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key
from app.data.official_sources import OFFICIAL_SOURCE_CATALOG
from app.models.news import NewsItem
from app.models.stock import Stock
from app.services.official_ingest import get_source_runner
from app.services.source_health import (
    get_all_source_health,
    get_source_health_history,
    summarize_source_runtime,
)

router = APIRouter()


def _parse_runtime_ts(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def _resolve_source_health_status(
    source: dict[str, str],
    runtime: dict[str, Any],
) -> tuple[str, Optional[float]]:
    if source.get("ingest_status") != "active":
        return "not_run", None

    now = datetime.now(timezone.utc)
    last_success = _parse_runtime_ts(runtime.get("last_successful_fetch"))
    if last_success is None:
        return "missing", None

    age_minutes = (now - last_success).total_seconds() / 60
    warn_after_hours = float(source.get("warn_after_hours") or 24)
    warn_after_minutes = warn_after_hours * 60

    last_error = runtime.get("last_error")
    last_error_at = _parse_runtime_ts(runtime.get("last_error_at"))
    if last_error and last_error_at and last_error_at >= last_success:
        return "failing", round(age_minutes, 1)

    if age_minutes > warn_after_minutes:
        return "stale", round(age_minutes, 1)

    return "fresh", round(age_minutes, 1)


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Başlatma script'i ve canlı kontrol için küçük sağlık yanıtı."""
    stock_count = (
        await db.execute(select(func.count(Stock.id)).where(Stock.is_active))
    ).scalar() or 0
    latest_kap = (
        await db.execute(select(func.max(NewsItem.created_at)).where(NewsItem.source == "KAP"))
    ).scalar_one_or_none()

    return {
        "status": "ok",
        "stocks_in_db": stock_count,
        "sources": {
            "kap": {
                "status": "fresh" if latest_kap else "missing",
                "last_seen": latest_kap.isoformat() if latest_kap else None,
            }
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/dashboard")
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Ana dashboard için gerçek DB kayıtlarından hızlı özet."""
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

    def stock_to_dict(stock: Stock):
        return {
            "symbol": stock.symbol,
            "name": stock.name,
            "sector": stock.sector,
            "current_price": stock.current_price,
            "daily_change_pct": stock.daily_change_pct,
            "volume": stock.volume,
            "market_cap": stock.market_cap,
            "overall_score": stock.overall_score,
            "recommendation": stock.recommendation,
            "is_bist30": stock.is_bist30,
            "technical_score": stock.technical_score,
            "fundamental_score": stock.fundamental_score,
            "sentiment_score": stock.sentiment_score,
        }

    return {
        "top_buy": [stock_to_dict(stock) for stock in top_buy],
        "top_sell": [stock_to_dict(stock) for stock in top_sell],
        "top_gainers": [stock_to_dict(stock) for stock in top_gainers],
        "top_losers": [stock_to_dict(stock) for stock in top_losers],
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


@router.get("/sources/catalog")
async def get_source_catalog():
    runtime_map = get_all_source_health()
    items = []
    health_counts = {
        "fresh": 0,
        "failing": 0,
        "stale": 0,
        "missing": 0,
        "not_run": 0,
    }
    active = 0
    planned = 0
    scheduler_or_manual = 0
    on_demand = 0
    needs_attention = 0

    for source in OFFICIAL_SOURCE_CATALOG:
        source_key = source["key"]
        runtime = runtime_map.get(source_key, {})
        health_status, age_minutes = _resolve_source_health_status(source, runtime)
        if health_status in health_counts:
            health_counts[health_status] += 1

        if source.get("ingest_status") == "active":
            active += 1
        else:
            planned += 1

        if source.get("scan_mode") == "on_demand":
            on_demand += 1
        else:
            scheduler_or_manual += 1

        attention_required = (
            source.get("ingest_status") == "active"
            and health_status in {"failing", "stale", "missing"}
        )
        if attention_required:
            needs_attention += 1

        detail_payload = runtime.get("detail")
        detail = detail_payload if isinstance(detail_payload, dict) else {}
        summary = summarize_source_runtime(runtime)
        source_item = {
            "key": source_key,
            "name": source.get("name"),
            "url": source.get("url"),
            "category": source.get("category"),
            "ingest_status": source.get("ingest_status"),
            "priority": source.get("priority"),
            "scan_mode": source.get("scan_mode"),
            "status_note": source.get("status_note"),
            "api_endpoint": source.get("api_endpoint"),
            "runner_available": get_source_runner(source_key) is not None,
            "health_status": health_status,
            "health": detail,
            "health_detail": {
                "status": health_status,
                "last_seen": runtime.get("last_successful_fetch"),
                "age_minutes": age_minutes,
                "records": detail.get("stored_count"),
                "last_successful_fetch": runtime.get("last_successful_fetch"),
                "last_attempt_at": runtime.get("last_attempt_at"),
                "last_error": runtime.get("last_error"),
                "last_error_at": runtime.get("last_error_at"),
                "detail": detail,
                "last_outcome": summary.get("last_outcome"),
                "consecutive_failures": summary.get("consecutive_failures"),
                "success_rate": summary.get("success_rate"),
                "recent_outcomes": summary.get("recent_outcomes"),
                "history_size": summary.get("history_size"),
                "trend": summary.get("trend"),
                "alert_level": (
                    "critical"
                    if health_status == "failing"
                    else "warning"
                    if health_status == "stale"
                    else "watch"
                    if health_status == "missing"
                    else "planned"
                    if source.get("ingest_status") != "active"
                    else "ok"
                ),
                "attention_required": attention_required,
                "attention_reason": (
                    f"{source.get('name')} kaynağı {health_status} durumda."
                    if attention_required
                    else None
                ),
            },
        }
        items.append(source_item)

    return {
        "sources": items,
        "summary": {
            "total": len(items),
            "active": active,
            "planned": planned,
            "scheduler_or_manual": scheduler_or_manual,
            "on_demand": on_demand,
            "needs_attention": needs_attention,
            "health": health_counts,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/sources/health/history")
async def get_sources_health_history(
    source_key: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    items = get_source_health_history(source_key=source_key, limit=limit)
    return {
        "items": items,
        "source_key": source_key,
        "limit": limit,
        "count": len(items),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/sources/scan/{source_key}")
async def scan_source_now(
    source_key: str,
    _: None = Depends(verify_api_key),
):
    runner = get_source_runner(source_key)
    if runner is None:
        raise HTTPException(status_code=404, detail=f"Kaynak tarayıcı bulunamadı: {source_key}")

    try:
        stored_count = await runner()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Kaynak taraması başarısız: {exc}") from exc

    return {
        "source_key": source_key,
        "stored_count": stored_count,
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
