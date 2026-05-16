"""Frontend'in kullandığı temel sistem ve dashboard endpoint'leri."""
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key
from app.core.config import settings
from app.data.official_sources import OFFICIAL_SOURCE_CATALOG
from app.models.news import NewsItem
from app.models.portfolio_v2 import PortfolioPosition
from app.models.price import CommodityPrice, PriceHistory
from app.models.signal import SignalDecisionSnapshot
from app.models.stock import Stock
from app.services.official_ingest import get_source_runner
from app.services.source_health import (
    get_all_source_health,
    get_source_health_history,
    summarize_source_runtime,
)

router = APIRouter()


def _diagnostic_item(
    key: str,
    title: str,
    status: str,
    detail: str,
    remediation: str,
    metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    return {
        "key": key,
        "title": title,
        "status": status,
        "detail": detail,
        "remediation": remediation,
        "metadata": metadata or {},
    }


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
        "canonical_universe_count": len(settings.BIST_FULL_SYMBOLS),
        "universe_sync": stock_count >= len(settings.BIST_FULL_SYMBOLS),
        "sources": {
            "kap": {
                "status": "fresh" if latest_kap else "missing",
                "last_seen": latest_kap.isoformat() if latest_kap else None,
            }
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/system/diagnostics")
async def get_system_diagnostics(db: AsyncSession = Depends(get_db)):
    """Hidden operator dashboard feed: reports working, degraded, and broken subsystems."""
    now = datetime.now(timezone.utc)
    items: list[dict[str, Any]] = []

    stock_count = (
        await db.execute(select(func.count(Stock.id)).where(Stock.is_active))
    ).scalar() or 0
    items.append(
        _diagnostic_item(
            key="db.stocks",
            title="Aktif hisse evreni",
            status="ok" if stock_count > 0 else "critical",
            detail=f"{stock_count} aktif hisse kayıtlı.",
            remediation="Initial load veya stock universe seed işlemini çalıştır.",
            metadata={"active_stock_count": stock_count},
        )
    )

    latest_price = (
        await db.execute(select(func.max(PriceHistory.date)))
    ).scalar_one_or_none()
    price_count = (await db.execute(select(func.count(PriceHistory.id)))).scalar() or 0
    price_age_days = (now.date() - latest_price).days if latest_price else None
    if latest_price is None:
        price_status = "critical"
        price_detail = "Fiyat geçmişi hiç yok."
    elif price_age_days is not None and price_age_days > 4:
        price_status = "critical"
        price_detail = f"Son fiyat verisi {price_age_days} gün eski."
    elif price_age_days is not None and price_age_days > 2:
        price_status = "warning"
        price_detail = f"Son fiyat verisi {price_age_days} gün eski."
    else:
        price_status = "ok"
        price_detail = f"Son fiyat tarihi {latest_price.isoformat()}."
    items.append(
        _diagnostic_item(
            key="market.price_history",
            title="Hisse fiyat verisi",
            status=price_status,
            detail=price_detail,
            remediation="Data update job veya yfinance canlı fiyat yenilemesini çalıştır.",
            metadata={"price_rows": price_count, "latest_price_date": latest_price.isoformat() if latest_price else None},
        )
    )

    commodity_symbols = ["XU100.IS", "USDTRY=X", "GC=F"]
    commodity_rows = (
        await db.execute(
            select(CommodityPrice.symbol, func.max(CommodityPrice.date), func.count(CommodityPrice.id))
            .where(CommodityPrice.symbol.in_(commodity_symbols))
            .group_by(CommodityPrice.symbol)
        )
    ).all()
    commodity_map = {symbol: {"latest": latest, "count": count} for symbol, latest, count in commodity_rows}
    missing_market = [symbol for symbol in commodity_symbols if symbol not in commodity_map]
    stale_market = [
        symbol
        for symbol, payload in commodity_map.items()
        if payload["latest"] and (now.date() - payload["latest"]).days > 4
    ]
    market_status = "critical" if missing_market else "warning" if stale_market else "ok"
    items.append(
        _diagnostic_item(
            key="market.reference_data",
            title="Referans piyasa verisi",
            status=market_status,
            detail=(
                f"Eksik: {', '.join(missing_market)}"
                if missing_market
                else f"Eski: {', '.join(stale_market)}"
                if stale_market
                else "BIST100, USDTRY ve altın referans verileri mevcut."
            ),
            remediation="Market data update job veya commodity/index backfill çalıştır.",
            metadata={
                "symbols": {
                    k: {"latest": v["latest"].isoformat() if v["latest"] else None, "count": v["count"]}
                    for k, v in commodity_map.items()
                }
            },
        )
    )

    from app.core.config import settings

    items.append(
        _diagnostic_item(
            key="llm.openai",
            title="OpenAI yapılandırması",
            status="ok" if bool(settings.OPENAI_API_KEY) else "critical",
            detail=(
                f"OpenAI anahtarı mevcut; model {settings.OPENAI_MODEL}."
                if settings.OPENAI_API_KEY
                else "OPENAI_API_KEY tanımlı değil."
            ),
            remediation="Backend ortam değişkenlerine OPENAI_API_KEY ve OPENAI_MODEL ekle.",
            metadata={"model": settings.OPENAI_MODEL, "configured": bool(settings.OPENAI_API_KEY)},
        )
    )

    runtime_map = get_all_source_health()
    active_source_findings = []
    for source in OFFICIAL_SOURCE_CATALOG:
        runtime = runtime_map.get(source["key"], {})
        status, age_minutes = _resolve_source_health_status(source, runtime)
        if source.get("ingest_status") == "active" and status in {"failing", "stale", "missing"}:
            active_source_findings.append({
                "key": source["key"],
                "name": source.get("name"),
                "status": status,
                "age_minutes": age_minutes,
                "last_error": runtime.get("last_error"),
            })
    items.append(
        _diagnostic_item(
            key="sources.official",
            title="Resmi kaynak taramaları",
            status="critical" if any(f["status"] == "failing" for f in active_source_findings) else "warning" if active_source_findings else "ok",
            detail=(
                f"{len(active_source_findings)} aktif kaynak ilgi istiyor."
                if active_source_findings
                else "Aktif resmi kaynaklarda açık hata yok."
            ),
            remediation="Kaynak detayında son hatayı incele; gerekirse /api/sources/scan/{source_key} ile manuel tara.",
            metadata={"findings": active_source_findings},
        )
    )

    latest_snapshot = (
        await db.execute(select(func.max(SignalDecisionSnapshot.decision_date)))
    ).scalar_one_or_none()
    snapshot_count = (await db.execute(select(func.count(SignalDecisionSnapshot.id)))).scalar() or 0
    snapshot_age_days = (now.date() - latest_snapshot).days if latest_snapshot else None
    signal_status = "critical" if latest_snapshot is None else "warning" if snapshot_age_days is not None and snapshot_age_days > 3 else "ok"
    items.append(
        _diagnostic_item(
            key="signals.snapshots",
            title="Sinyal snapshot döngüsü",
            status=signal_status,
            detail=(
                "Henüz sinyal snapshot yok."
                if latest_snapshot is None
                else f"Son snapshot {latest_snapshot.isoformat()}, toplam {snapshot_count} kayıt."
            ),
            remediation="Sinyal Merkezi'nde Bugünü Kaydet veya scheduler background_signal_snapshot çalışmalı.",
            metadata={"latest_snapshot_date": latest_snapshot.isoformat() if latest_snapshot else None, "snapshot_count": snapshot_count},
        )
    )

    measured_count = (
        await db.execute(
            select(func.count(SignalDecisionSnapshot.id)).where(SignalDecisionSnapshot.actual_return_1w_pct.isnot(None))
        )
    ).scalar() or 0
    items.append(
        _diagnostic_item(
            key="signals.outcomes",
            title="Sinyal sonuç ölçümü",
            status="warning" if measured_count < 20 else "ok",
            detail=f"{measured_count} ölçülmüş 1 haftalık sinyal var.",
            remediation="20+ ölçülmüş sinyal birikene kadar kalibrasyon observation modunda kalır.",
            metadata={"measured_1w_count": measured_count, "minimum_for_calibration": 20},
        )
    )

    backtest_ready = stock_count > 0 and price_count >= 1000 and "XU100.IS" in commodity_map
    items.append(
        _diagnostic_item(
            key="strategy.backtest",
            title="Backtest altyapısı",
            status="ok" if backtest_ready else "critical",
            detail=(
                "Strateji backtest için hisse fiyatları ve BIST100 benchmark hazır."
                if backtest_ready
                else "Backtest için fiyat geçmişi veya BIST100 benchmark eksik."
            ),
            remediation="Hisse fiyat geçmişi ve XU100.IS referans verisini güncelle.",
            metadata={"price_rows": price_count, "has_benchmark": "XU100.IS" in commodity_map},
        )
    )

    active_positions = (
        await db.execute(select(func.count(PortfolioPosition.id)).where(PortfolioPosition.is_active == True))  # noqa: E712
    ).scalar() or 0
    items.append(
        _diagnostic_item(
            key="risk.alerts",
            title="Risk ve alarm denetçisi",
            status="ok",
            detail=f"Risk denetçisi çalışır durumda; {active_positions} aktif pozisyon izleniyor.",
            remediation="Pozisyon yoksa alarm motoru yalnızca KAP, model skoru ve yeni sinyalleri izler.",
            metadata={"active_positions": active_positions},
        )
    )

    try:
        from app.main import scheduler

        scheduler_jobs = {job.func.__name__ for job in scheduler.get_jobs()}
        expected_jobs = {
            "background_signal_snapshot",
            "background_signal_outcome_evaluation",
            "background_data_update",
            "background_kap_scan",
        }
        missing_jobs = sorted(expected_jobs - scheduler_jobs)
        scheduler_running = bool(getattr(scheduler, "running", False))
        scheduler_status = "critical" if not scheduler_running or missing_jobs else "ok"
        items.append(
            _diagnostic_item(
                key="scheduler.jobs",
                title="Zamanlanmış işler",
                status=scheduler_status,
                detail=(
                    "Scheduler çalışıyor ve kritik işler kayıtlı."
                    if scheduler_status == "ok"
                    else f"Scheduler running={scheduler_running}, eksik işler: {', '.join(missing_jobs) or 'yok'}."
                ),
                remediation="Backend lifespan başlatıldığından ve APScheduler job kayıtlarından emin ol.",
                metadata={"running": scheduler_running, "job_count": len(scheduler_jobs), "missing_jobs": missing_jobs},
            )
        )
    except Exception as exc:
        items.append(
            _diagnostic_item(
                key="scheduler.jobs",
                title="Zamanlanmış işler",
                status="critical",
                detail=f"Scheduler okunamadı: {exc}",
                remediation="backend/app/main.py scheduler başlangıcını incele.",
            )
        )

    status_rank = {"ok": 0, "warning": 1, "critical": 2}
    worst = max(items, key=lambda item: status_rank[item["status"]])["status"]
    overall = "down" if worst == "critical" else "degraded" if worst == "warning" else "healthy"
    return {
        "status": overall,
        "summary": {
            "ok": sum(1 for item in items if item["status"] == "ok"),
            "warning": sum(1 for item in items if item["status"] == "warning"),
            "critical": sum(1 for item in items if item["status"] == "critical"),
            "total": len(items),
        },
        "items": items,
        "timestamp": now.isoformat(),
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
