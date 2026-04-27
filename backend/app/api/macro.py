from __future__ import annotations

"""Macro domain router — TCMB, TUIK makro veri taramaları ve makro olay akışı."""
import asyncio
import logging
import re
import time
import requests
import yfinance as yf
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.news import NewsItem
from app.models.price import CommodityPrice
from app.models.stock import Stock

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/macro/tcmb/scan")
async def trigger_tcmb_scan():
    """TCMB makro veri taramasını manuel tetikle."""
    from app.services.tcmb_adapter import run_tcmb_scan

    stored = await run_tcmb_scan()
    _indicators_cache.clear()
    return {
        "status": "completed",
        "stored": stored,
        "source": "TCMB",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/macro/tuik/scan")
async def trigger_tuik_scan():
    """TUIK ekonomik veri taramasını manuel tetikle."""
    from app.services.tuik_adapter import run_tuik_scan

    stored = await run_tuik_scan()
    _indicators_cache.clear()
    return {
        "status": "completed",
        "stored": stored,
        "source": "TUIK",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/macro/events")
async def get_macro_events(limit: int = 20, days: int = 7):
    """Son N gündeki makro olayları getir (KAP, TCMB, TUIK haber akışı)."""
    async with AsyncSessionLocal() as db:
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)

        result = await db.execute(
            select(NewsItem, Stock)
            .join(Stock, NewsItem.stock_id == Stock.id)
            .filter(
                NewsItem.published_at >= cutoff_time,
                NewsItem.category.in_(["macro", "company"])
            )
            .order_by(NewsItem.published_at.desc())
            .limit(limit)
        )

        events = []
        for news, stock in result.all():
            events.append({
                "id": news.id,
                "title": news.title,
                "summary": news.summary,
                "source": news.source,
                "symbol": stock.symbol,
                "sentiment_score": news.sentiment_score,
                "sentiment_label": news.sentiment_label,
                "importance_score": news.importance_score,
                "published_at": news.published_at.isoformat(),
                "category": news.category,
            })

        return {
            "events": events,
            "total": len(events),
            "filtered_by_days": days,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Module-level simple cache (sufficient for single-worker FastAPI)
_indicators_cache: dict = {}
_indicators_cache_ttl = 60  # seconds


async def _fetch_last_close(symbol: str) -> Optional[float]:
    loop = asyncio.get_event_loop()

    def _sync_fetch():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d", interval="1d", auto_adjust=True)
            if hist is None or hist.empty:
                return None
            close = hist["Close"].dropna()
            return float(close.iloc[-1]) if not close.empty else None
        except Exception:
            return None

    return await loop.run_in_executor(None, _sync_fetch)


async def _fetch_last_close_with_date(symbol: str) -> Tuple[Optional[float], Optional[str]]:
    loop = asyncio.get_event_loop()

    def _sync_fetch():
        try:
            response = requests.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                params={"range": "1mo", "interval": "1d", "includePrePost": "false"},
                timeout=20,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            response.raise_for_status()
            payload = response.json()
            result = ((payload.get("chart") or {}).get("result") or [None])[0] or {}
            timestamps = result.get("timestamp") or []
            closes = (((result.get("indicators") or {}).get("quote") or [{}])[0] or {}).get("close") or []
            paired = [
                (ts, close)
                for ts, close in zip(timestamps, closes)
                if close is not None
            ]
            if not paired:
                return None, None
            ts, close = paired[-1]
            as_of = datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
            return float(close), as_of
        except Exception:
            return None, None

    return await loop.run_in_executor(None, _sync_fetch)


def _extract_percentage(text: str) -> Optional[float]:
    if not text:
        return None

    match = re.search(r"%\s*(\d+[.,]?\d*)", text)
    if not match:
        match = re.search(r"(\d+[.,]?\d*)\s*%", text)
    if not match:
        match = re.search(r"(\d+[.,]\d+|\d+)", text)
    if not match:
        return None

    try:
        return float(match.group(1).replace(",", "."))
    except ValueError:
        return None


async def _latest_macro_reading(source: str, title_prefix: str) -> Tuple[Optional[float], Optional[str]]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(NewsItem)
            .where(
                NewsItem.source == source,
                NewsItem.title.ilike(f"{title_prefix}%"),
            )
            .order_by(NewsItem.published_at.desc(), NewsItem.id.desc())
            .limit(1)
        )
        item = result.scalar_one_or_none()

    if not item:
        return None, None

    value = _extract_percentage(item.title) or _extract_percentage(item.summary or "")
    as_of = item.published_at.isoformat() if item.published_at else None
    return value, as_of


async def _latest_market_reading(symbol: str) -> Tuple[Optional[float], Optional[str]]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(CommodityPrice)
            .where(CommodityPrice.symbol == symbol)
            .order_by(CommodityPrice.date.desc(), CommodityPrice.id.desc())
            .limit(1)
        )
        item = result.scalar_one_or_none()

    if not item:
        return None, None

    as_of = item.date.isoformat() if item.date else None
    return float(item.close), as_of


def _market_reading_is_stale(as_of: Optional[str], max_age_days: int = 2) -> bool:
    if not as_of:
        return True
    try:
        reading_date = datetime.fromisoformat(as_of).date()
    except ValueError:
        try:
            reading_date = datetime.strptime(as_of, "%Y-%m-%d").date()
        except ValueError:
            return True
    return (datetime.now(timezone.utc).date() - reading_date).days > max_age_days


@router.get("/macro/indicators")
async def get_macro_indicators():
    """
    Live macro göstergeleri: USD/TRY, altın (TRY), BIST100 endeksi.
    Faiz ve enflasyon en son TCMB/TUIK kayıtlarından okunur. 60 saniyelik önbellek.
    """
    global _indicators_cache

    now = time.time()
    if _indicators_cache.get("ts") and now - _indicators_cache["ts"] < _indicators_cache_ttl:
        return _indicators_cache["data"]

    try:
        (usdtry, usdtry_as_of), (gold_usd, gold_as_of), (bist100, bist100_as_of) = await asyncio.gather(
            _latest_market_reading("USDTRY=X"),
            _latest_market_reading("GC=F"),
            _latest_market_reading("XU100.IS"),
        )

        live_needed = (
            usdtry is None
            or gold_usd is None
            or bist100 is None
            or _market_reading_is_stale(usdtry_as_of, max_age_days=2)
            or _market_reading_is_stale(gold_as_of, max_age_days=2)
            or _market_reading_is_stale(bist100_as_of, max_age_days=4)
        )

        if live_needed:
            (live_usdtry, live_usdtry_as_of), (live_gold_usd, live_gold_as_of), (live_bist100, live_bist100_as_of) = await asyncio.gather(
                _fetch_last_close_with_date("USDTRY=X"),
                _fetch_last_close_with_date("GC=F"),
                _fetch_last_close_with_date("XU100.IS"),
            )
            if live_usdtry is not None and (_market_reading_is_stale(usdtry_as_of, max_age_days=2) or usdtry is None):
                usdtry, usdtry_as_of = live_usdtry, live_usdtry_as_of
            if live_gold_usd is not None and (_market_reading_is_stale(gold_as_of, max_age_days=2) or gold_usd is None):
                gold_usd, gold_as_of = live_gold_usd, live_gold_as_of
            if live_bist100 is not None and (_market_reading_is_stale(bist100_as_of, max_age_days=4) or bist100 is None):
                bist100, bist100_as_of = live_bist100, live_bist100_as_of

        # Convert gold USD/oz → TRY/gram  (1 troy oz = 31.1035 g)
        gold_try = (gold_usd * usdtry / 31.1035) if (gold_usd and usdtry) else None

        interest_rate, interest_rate_as_of = await _latest_macro_reading("TCMB", "TCMB Politika Faiz Oranı")
        inflation_rate, inflation_rate_as_of = await _latest_macro_reading("TUIK", "TUIK TÜFE Enflasyon")

        result = {
            "usdtry": round(usdtry, 4) if usdtry else None,
            "gold_try": round(gold_try, 2) if gold_try else None,
            "bist100": round(bist100, 2) if bist100 else None,
            "usdtry_as_of": usdtry_as_of,
            "gold_try_as_of": gold_as_of,
            "bist100_as_of": bist100_as_of,
            "interest_rate": round(interest_rate, 2) if interest_rate is not None else None,
            "inflation_rate": round(inflation_rate, 2) if inflation_rate is not None else None,
            "interest_rate_as_of": interest_rate_as_of,
            "inflation_rate_as_of": inflation_rate_as_of,
            "as_of": datetime.now(timezone.utc).isoformat(),
        }

        _indicators_cache["data"] = result
        _indicators_cache["ts"] = now
        return result

    except Exception as exc:
        logger.error(f"Macro indicators fetch failed: {exc}")
        raise HTTPException(status_code=503, detail=f"Makro veri alınamadı: {exc}")
