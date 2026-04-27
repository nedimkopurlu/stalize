"""Model portföy API router — MPRT-03, MPRT-05"""
import logging
from datetime import date, datetime, timezone
from typing import Optional, List
import asyncio

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, desc
import yfinance as yf

from app.core.database import AsyncSessionLocal
from app.models.portfolio_v2 import PortfolioPosition, PortfolioDailySnapshot, PortfolioChangeLog
from app.services.portfolio_snapshot import _fetch_close_price

router = APIRouter()
logger = logging.getLogger(__name__)


async def _fetch_benchmark_history(days: int) -> dict[str, float]:
    """BIST100 kapanış serisini date->close map olarak getir."""
    loop = asyncio.get_event_loop()

    def _sync_fetch():
        try:
            data = yf.download("XU100.IS", period=f"{max(days + 10, 30)}d", interval="1d", progress=False)
            if data is None or data.empty:
                return {}
            close = data["Close"]
            output: dict[str, float] = {}
            for idx, value in close.dropna().items():
                date_key = idx.date().isoformat() if hasattr(idx, "date") else str(idx).split(" ")[0]
                output[date_key] = float(value)
            return output
        except Exception as exc:
            logger.warning(f"BIST100 benchmark çekilemedi: {exc}")
            return {}

    return await loop.run_in_executor(None, _sync_fetch)


# ─── Pydantic Request Modelleri ────────────────────────────────────────────

class PositionCreate(BaseModel):
    symbol: str                        # "THYAO" formatında (uzantısız)
    entry_price: float
    quantity: float
    entry_date: date
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    rationale: Optional[str] = None


class ChangeLogCreate(BaseModel):
    date: date
    action: str                        # "ADD" veya "REMOVE"
    symbol: str
    reason: Optional[str] = None


# ─── Endpoint 1: GET /portfolio/positions ──────────────────────────────────

@router.get("/portfolio/positions")
async def get_positions():
    """
    Aktif pozisyonları gerçek yfinance fiyatıyla döner.
    Fiyat çekilemezse current_price=None, pnl_pct=None döner — hata fırlatmaz.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(PortfolioPosition).where(PortfolioPosition.is_active == True)  # noqa: E712
        )
        positions = result.scalars().all()

    output = []
    for pos in positions:
        yahoo_symbol = f"{pos.symbol}.IS"
        current_price = await _fetch_close_price(yahoo_symbol)

        pnl_pct = None
        if current_price is not None:
            pnl_pct = round(((current_price - pos.entry_price) / pos.entry_price) * 100, 4)

        output.append({
            "id": pos.id,
            "symbol": pos.symbol,
            "entry_price": pos.entry_price,
            "quantity": pos.quantity,
            "entry_date": pos.entry_date.isoformat(),
            "stop_loss": pos.stop_loss,
            "target_price": pos.target_price,
            "rationale": pos.rationale,
            "current_price": current_price,
            "pnl_pct": pnl_pct,
        })

    logger.info(f"GET /portfolio/positions — {len(output)} aktif pozisyon döndü.")
    return output


# ─── Endpoint 2: GET /portfolio/history ────────────────────────────────────

@router.get("/portfolio/history")
async def get_history(days: int = Query(90, ge=1, le=365)):
    """Son N günün snapshot geçmişi + benchmark + risk özeti."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(PortfolioDailySnapshot)
            .order_by(desc(PortfolioDailySnapshot.date))
            .limit(days)
        )
        snapshots = result.scalars().all()

        positions_result = await db.execute(
            select(PortfolioPosition).where(PortfolioPosition.is_active == True)  # noqa: E712
        )
        positions = positions_result.scalars().all()

    snapshot_rows = list(reversed(snapshots))
    benchmark_map = await _fetch_benchmark_history(days)

    portfolio_series = []
    benchmark_series = []

    base_portfolio_value = next((s.total_value for s in snapshot_rows if s.total_value), None)
    first_benchmark_value = None
    for snapshot in snapshot_rows:
        if snapshot.date.isoformat() in benchmark_map:
            first_benchmark_value = benchmark_map[snapshot.date.isoformat()]
            break

    for snapshot in snapshot_rows:
        date_key = snapshot.date.isoformat()
        total_value = snapshot.total_value
        benchmark_close = benchmark_map.get(date_key)

        portfolio_return_pct = None
        if total_value is not None and base_portfolio_value not in (None, 0):
            portfolio_return_pct = round(((total_value - base_portfolio_value) / base_portfolio_value) * 100, 4)

        benchmark_return_pct = None
        if benchmark_close is not None and first_benchmark_value not in (None, 0):
            benchmark_return_pct = round(((benchmark_close - first_benchmark_value) / first_benchmark_value) * 100, 4)

        portfolio_series.append({
            "date": date_key,
            "value": total_value,
            "return_pct": portfolio_return_pct,
            "daily_pnl_pct": snapshot.daily_pnl_pct,
        })
        benchmark_series.append({
            "date": date_key,
            "close": round(benchmark_close, 2) if benchmark_close is not None else None,
            "return_pct": benchmark_return_pct,
        })

    total_positions = len(positions)
    positions_at_risk = 0
    positions_near_target = 0
    for pos in positions:
        current_price = await _fetch_close_price(f"{pos.symbol}.IS")
        if current_price is None:
            continue
        if pos.stop_loss is not None and current_price <= pos.stop_loss:
            positions_at_risk += 1
        if pos.target_price is not None and current_price >= pos.target_price * 0.97:
            positions_near_target += 1

    latest_portfolio_return = portfolio_series[-1]["return_pct"] if portfolio_series else None
    latest_benchmark_return = benchmark_series[-1]["return_pct"] if benchmark_series else None
    active_return_spread = None
    if latest_portfolio_return is not None and latest_benchmark_return is not None:
        active_return_spread = round(latest_portfolio_return - latest_benchmark_return, 4)

    return {
        "snapshots": [
            {
                "id": s.id,
                "date": s.date.isoformat(),
                "total_value": s.total_value,
                "daily_pnl_pct": s.daily_pnl_pct,
                "positions_json": s.positions_json,
            }
            for s in snapshots
        ],
        "comparison": {
            "portfolio_series": portfolio_series,
            "benchmark_series": benchmark_series,
            "benchmark_symbol": "XU100.IS",
            "benchmark_label": "BIST100",
            "active_return_spread": active_return_spread,
        },
        "risk_summary": {
            "active_positions": total_positions,
            "positions_at_risk": positions_at_risk,
            "positions_near_target": positions_near_target,
            "latest_portfolio_return_pct": latest_portfolio_return,
            "latest_benchmark_return_pct": latest_benchmark_return,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─── Endpoint 3: POST /portfolio/positions ─────────────────────────────────

@router.post("/portfolio/positions", status_code=201)
async def add_position(body: PositionCreate):
    """
    Yeni pozisyon ekle + change_log'a ADD kaydı yaz.
    Sistem otomatik pozisyon açmaz — bu endpoint manuel çağrı içindir.
    """
    symbol = body.symbol.upper()

    async with AsyncSessionLocal() as db:
        pos = PortfolioPosition(
            symbol=symbol,
            entry_price=body.entry_price,
            quantity=body.quantity,
            entry_date=body.entry_date,
            stop_loss=body.stop_loss,
            target_price=body.target_price,
            rationale=body.rationale,
            is_active=True,
        )
        db.add(pos)
        await db.flush()  # id oluşsun

        log_entry = PortfolioChangeLog(
            date=datetime.now(timezone.utc).date(),
            action="ADD",
            symbol=symbol,
            reason=body.rationale,
        )
        db.add(log_entry)
        await db.commit()

        pos_id = pos.id

    logger.info(f"POST /portfolio/positions — {symbol} eklendi (id={pos_id}).")
    return {"id": pos_id, "symbol": symbol, "status": "added"}


# ─── Endpoint 4: DELETE /portfolio/positions/{position_id} ─────────────────

@router.delete("/portfolio/positions/{position_id}")
async def close_position(position_id: int):
    """
    Pozisyonu kapat (soft delete — is_active=False).
    change_log'a REMOVE kaydı yazar.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(PortfolioPosition).where(PortfolioPosition.id == position_id)
        )
        pos = result.scalar_one_or_none()
        if not pos:
            raise HTTPException(status_code=404, detail=f"Pozisyon bulunamadı: id={position_id}")

        pos.is_active = False
        symbol = pos.symbol

        log_entry = PortfolioChangeLog(
            date=datetime.now(timezone.utc).date(),
            action="REMOVE",
            symbol=symbol,
            reason=None,
        )
        db.add(log_entry)
        await db.commit()

    logger.info(f"DELETE /portfolio/positions/{position_id} — {symbol} kapatıldı.")
    return {"status": "closed", "symbol": symbol}


# ─── Endpoint 5: POST /portfolio/change-log ────────────────────────────────

@router.post("/portfolio/change-log", status_code=201)
async def add_change_log(body: ChangeLogCreate):
    """
    Doğrudan change_log girişi oluştur.
    action "ADD" veya "REMOVE" dışında bir değerse 422 döner.
    """
    if body.action not in ("ADD", "REMOVE"):
        raise HTTPException(
            status_code=422,
            detail=f"Geçersiz action: '{body.action}'. Sadece 'ADD' veya 'REMOVE' kabul edilir."
        )

    async with AsyncSessionLocal() as db:
        log_entry = PortfolioChangeLog(
            date=body.date,
            action=body.action,
            symbol=body.symbol.upper(),
            reason=body.reason,
        )
        db.add(log_entry)
        await db.commit()
        log_id = log_entry.id

    logger.info(f"POST /portfolio/change-log — {body.action} {body.symbol} (id={log_id}).")
    return {"id": log_id, "status": "logged"}
