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
