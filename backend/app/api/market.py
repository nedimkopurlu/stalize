"""Market domain router — BIST100 endeks, döviz, altın ve fırsat skoru endpoints (Phase 28)."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.price import CommodityPrice
from app.models.stock import Stock

router = APIRouter()
logger = logging.getLogger(__name__)

# Module-level TTL cache (mirrors macro.py pattern)
_market_cache: dict = {}
_market_cache_ttl = 60  # seconds

# Turkish gold coin nominal weights (22-karat); see 28-RESEARCH.md "Pitfall 2"
GOLD_COIN_WEIGHTS: Dict[str, float] = {
    "gram": 1.0,
    "ons": 31.1035,
    "ceyrek": 1.754,
    "yarim": 3.508,
    "tam": 7.016,
}

# Forex pairs exposed via /market/forex (subset of settings.CURRENCY_PAIRS)
FOREX_PAIRS: Dict[str, str] = {
    "USDTRY=X": "USD/TRY",
    "EURTRY=X": "EUR/TRY",
    "GBPTRY=X": "GBP/TRY",
    "CNYTRY=X": "CNY/TRY",
    "JPYTRY=X": "JPY/TRY",
    "CHFTRY=X": "CHF/TRY",
}


@router.get("/market/health")
async def market_health() -> dict:
    """Lightweight health probe for the market router (used by tests)."""
    return {
        "status": "ok",
        "router": "market",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/market/bist100")
async def get_bist100_summary(db: AsyncSession = Depends(get_db)) -> dict:
    """DASH-01: BIST100 endeks özeti — değer, günlük değişim, hacim.

    Strategy:
    1. Read latest 2 CommodityPrice rows where symbol='XU100.IS'.
    2. Compute daily_change_pct from last 2 closes; None if only 1 row.
    3. Volume: report None if 0 / NaN (XU100 index volume often unreliable — Pitfall 1).
    4. Returns 503 if no rows exist (do not fabricate values).
    """
    cache_key = "bist100"
    cached = _market_cache.get(cache_key)
    if cached and (datetime.now(timezone.utc).timestamp() - cached["ts"]) < _market_cache_ttl:
        return cached["data"]

    result = await db.execute(
        select(CommodityPrice)
        .where(CommodityPrice.symbol == "XU100.IS")
        .order_by(CommodityPrice.date.desc())
        .limit(2)
    )
    rows = result.scalars().all()
    if not rows:
        raise HTTPException(status_code=503, detail="BIST100 verisi yok")

    today = rows[0]
    yesterday = rows[1] if len(rows) > 1 else None

    change_pct: Optional[float] = None
    if yesterday and yesterday.close and today.close is not None:
        change_pct = (today.close - yesterday.close) / yesterday.close * 100

    # Pitfall 1: index volume often 0/NaN — surface as None, do not fabricate
    volume_val: Optional[float] = None
    if today.volume is not None and today.volume > 0:
        volume_val = float(today.volume)

    data = {
        "value": round(float(today.close), 2) if today.close is not None else None,
        "daily_change_pct": round(change_pct, 2) if change_pct is not None else None,
        "volume": volume_val,
        "as_of": today.date.isoformat(),
    }
    _market_cache[cache_key] = {"ts": datetime.now(timezone.utc).timestamp(), "data": data}
    return data


@router.get("/market/forex")
async def get_forex_rates(db: AsyncSession = Depends(get_db)) -> dict:
    """DASH-02: 5-10 forex çifti — kur ve günlük değişim.

    Iterates FOREX_PAIRS and reads the latest 2 CommodityPrice rows per symbol.
    Computes daily_change_pct from those two rows (Pitfall 6: do NOT trust
    CommodityPrice.change_pct field — it is often NULL).
    Pairs with no DB rows are silently skipped; pairs with 1 row report
    daily_change_pct=None but are still included.
    """
    cache_key = "forex"
    cached = _market_cache.get(cache_key)
    if cached and (datetime.now(timezone.utc).timestamp() - cached["ts"]) < _market_cache_ttl:
        return cached["data"]

    pairs_out = []
    for symbol, name in FOREX_PAIRS.items():
        res = await db.execute(
            select(CommodityPrice)
            .where(CommodityPrice.symbol == symbol)
            .order_by(CommodityPrice.date.desc())
            .limit(2)
        )
        rows = res.scalars().all()
        if not rows:
            continue
        today = rows[0]
        yesterday = rows[1] if len(rows) > 1 else None
        change_pct: Optional[float] = None
        if yesterday and yesterday.close and today.close is not None:
            change_pct = (today.close - yesterday.close) / yesterday.close * 100
        pairs_out.append({
            "symbol": symbol,
            "name": name,
            "rate": round(float(today.close), 4) if today.close is not None else None,
            "daily_change_pct": round(change_pct, 2) if change_pct is not None else None,
            "as_of": today.date.isoformat(),
        })

    data = {
        "pairs": pairs_out,
        "count": len(pairs_out),
        "as_of": datetime.now(timezone.utc).isoformat(),
    }
    _market_cache[cache_key] = {"ts": datetime.now(timezone.utc).timestamp(), "data": data}
    return data


async def _latest_close_and_date(db: AsyncSession, symbol: str) -> Tuple[Optional[float], Optional[str]]:
    """Local helper: latest CommodityPrice (close, ISO date) for a symbol."""
    res = await db.execute(
        select(CommodityPrice)
        .where(CommodityPrice.symbol == symbol)
        .order_by(CommodityPrice.date.desc())
        .limit(1)
    )
    row = res.scalars().first()
    if row is None or row.close is None:
        return None, None
    return float(row.close), row.date.isoformat()


@router.get("/market/opportunities")
async def get_opportunities(
    limit: int = Query(20, ge=1, le=50, description="Top N stocks by overall_score"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """DISC-02: 'Bugün ilginç hisseler' — BIST100 evreninde overall_score'a göre top N.

    Filters:
      - is_bist100 == True
      - is_active == True
      - overall_score IS NOT NULL  (Pitfall 3: stocks with NULL scores excluded)

    Ordered by overall_score DESC. No JOIN to Fundamental — score is denormalized
    on Stock by ScoringEngine.update_all_scores(); that is the source of truth.
    """
    # Note: opportunities are highly dynamic — we do NOT cache this endpoint to ensure
    # freshness immediately after scoring_engine.update_all_scores() runs.
    result = await db.execute(
        select(Stock)
        .where(Stock.is_bist100 == True)
        .where(Stock.is_active == True)
        .where(Stock.overall_score.isnot(None))
        .order_by(Stock.overall_score.desc())
        .limit(limit)
    )
    stocks = result.scalars().all()

    return {
        "stocks": [
            {
                "symbol": s.symbol,
                "name": s.name,
                "sector": s.sector,
                "current_price": s.current_price,
                "daily_change_pct": s.daily_change_pct,
                "overall_score": s.overall_score,
                "fundamental_score": s.fundamental_score,
                "technical_score": s.technical_score,
                "recommendation": s.recommendation,
            }
            for s in stocks
        ],
        "count": len(stocks),
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/market/bist100/history")
async def get_bist100_history(
    days: int = Query(30, ge=1, le=365, description="Son kaç günlük veri döndürülsün"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """BIST100 kapanış fiyatı geçmişi — tarih artan sırada, son `days` satır.

    Reads CommodityPrice rows where symbol='XU100.IS', ordered ASC, limited to
    the last `days` rows. Returns 503 if no data exists.
    """
    cache_key = f"bist100_history_{days}"
    cached = _market_cache.get(cache_key)
    if cached and (datetime.now(timezone.utc).timestamp() - cached["ts"]) < 300:
        return cached["data"]

    result = await db.execute(
        select(CommodityPrice)
        .where(CommodityPrice.symbol == "XU100.IS")
        .order_by(CommodityPrice.date.desc())
        .limit(days)
    )
    rows = result.scalars().all()
    if not rows:
        raise HTTPException(status_code=503, detail="BIST100 geçmişi yok")

    # Reverse to ascending date order for chart consumption
    rows_asc = list(reversed(rows))
    points = [
        {"date": row.date.isoformat(), "close": round(float(row.close), 2)}
        for row in rows_asc
        if row.close is not None
    ]

    data = {"points": points, "count": len(points)}
    _market_cache[cache_key] = {"ts": datetime.now(timezone.utc).timestamp(), "data": data}
    return data


@router.get("/market/gold")
async def get_gold_prices(db: AsyncSession = Depends(get_db)) -> dict:
    """DASH-03: Beş altın formu — gram, ons, çeyrek, yarım, tam (TRY).

    Formula: gram_try = gold_usd_per_oz * usdtry / 31.1035
    Each coin form = gram_try * GOLD_COIN_WEIGHTS[form].
    Coin weights are nominal 22-karat values (Pitfall 2).
    Returns 503 if either GC=F or USDTRY=X is missing.
    """
    cache_key = "gold"
    cached = _market_cache.get(cache_key)
    if cached and (datetime.now(timezone.utc).timestamp() - cached["ts"]) < _market_cache_ttl:
        return cached["data"]

    gold_usd, gold_as_of = await _latest_close_and_date(db, "GC=F")
    usdtry, _usdtry_as_of = await _latest_close_and_date(db, "USDTRY=X")

    if gold_usd is None or usdtry is None:
        raise HTTPException(status_code=503, detail="Altın verisi yok")

    gram_try = gold_usd * usdtry / 31.1035

    forms = {
        form: round(gram_try * weight, 2)
        for form, weight in GOLD_COIN_WEIGHTS.items()
    }

    data = {
        "forms": forms,
        "gold_usd_per_oz": round(gold_usd, 2),
        "usdtry": round(usdtry, 4),
        "as_of": gold_as_of,
    }
    _market_cache[cache_key] = {"ts": datetime.now(timezone.utc).timestamp(), "data": data}
    return data
