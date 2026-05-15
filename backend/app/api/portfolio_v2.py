"""Model portföy API router — MPRT-03, MPRT-05"""
import logging
import numpy as np
from datetime import date, datetime, timedelta, timezone
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy import select, desc, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key
from app.models.portfolio_v2 import PortfolioPosition, PortfolioDailySnapshot, PortfolioChangeLog
from app.models.stock import Stock
from app.models.price import CommodityPrice, PriceHistory
from app.services.data_collector import get_yahoo_chart_history
from app.services.portfolio_snapshot import _fetch_close_price

router = APIRouter()
logger = logging.getLogger(__name__)


async def _fetch_benchmark_history(days: int, db: AsyncSession) -> dict[str, float]:
    """BIST100 kapanış serisini date->close map olarak getir."""
    start = date.today() - timedelta(days=days + 10)
    result = await db.execute(
        select(CommodityPrice)
        .where(CommodityPrice.symbol == "XU100.IS", CommodityPrice.date >= start)
        .order_by(CommodityPrice.date.asc())
    )
    rows = result.scalars().all()
    if rows:
        return {row.date.isoformat(): float(row.close) for row in rows if row.close is not None}

    fallback_period = "1mo" if days <= 30 else "3mo" if days <= 90 else "1y"
    data = await get_yahoo_chart_history("XU100.IS", period=fallback_period)
    if data is None or data.empty:
        return {}

    output: dict[str, float] = {}
    for idx, row in data.iterrows():
        close = row.get("Close")
        if close is None:
            continue
        date_key = idx.date().isoformat() if hasattr(idx, "date") else str(idx).split(" ")[0]
        output[date_key] = float(close)
    return output


# ─── Pydantic Request Modelleri ────────────────────────────────────────────

class PositionCreate(BaseModel):
    symbol: str                        # "THYAO" formatında (uzantısız)
    entry_price: float
    quantity: float
    entry_date: date
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    rationale: Optional[str] = None
    invalidation_condition: Optional[str] = None


class PositionClose(BaseModel):
    exit_price: float
    exit_date: date
    exit_reason: Optional[str] = None


def _normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper().removesuffix(".IS")


def _validate_positive_number(value: Optional[float], field_name: str, required: bool = False) -> None:
    if value is None:
        if required:
            raise HTTPException(status_code=422, detail=f"{field_name} zorunludur")
        return
    if value <= 0:
        raise HTTPException(status_code=422, detail=f"{field_name} pozitif olmalıdır")


async def _ensure_active_stock(symbol: str, db: AsyncSession) -> Stock:
    result = await db.execute(
        select(Stock).where(Stock.symbol == symbol, Stock.is_active == True)  # noqa: E712
    )
    stock = result.scalar_one_or_none()
    if stock is None:
        raise HTTPException(status_code=404, detail=f"Aktif hisse bulunamadı: {symbol}")
    return stock


# ─── Endpoint 1: GET /portfolio/positions ──────────────────────────────────

@router.get("/portfolio/positions")
async def get_positions(db: AsyncSession = Depends(get_db)):
    """
    Aktif pozisyonları + son 30 günde kapatılanları gerçek yfinance fiyatıyla döner.
    Kapalı pozisyonlar için current_price=None döner (yfinance çağrısı yapılmaz).
    Fiyat çekilemezse current_price=None, pnl_pct=None döner — hata fırlatmaz.
    """
    cutoff = date.today() - timedelta(days=30)
    result = await db.execute(
        select(PortfolioPosition).where(
            or_(
                PortfolioPosition.is_active == True,  # noqa: E712
                and_(
                    PortfolioPosition.is_active == False,  # noqa: E712
                    PortfolioPosition.exit_date >= cutoff,
                ),
            )
        ).order_by(PortfolioPosition.is_active.desc(), PortfolioPosition.entry_date.desc())
    )
    positions = result.scalars().all()

    output = []
    for pos in positions:
        if pos.is_active:
            yahoo_symbol = f"{pos.symbol}.IS"
            current_price = await _fetch_close_price(yahoo_symbol)
            pnl_pct = None
            if current_price is not None:
                pnl_pct = round(((current_price - pos.entry_price) / pos.entry_price) * 100, 4)
        else:
            # Kapalı pozisyon — yfinance çağrısı yapma
            current_price = None
            pnl_pct = None

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
            "partial": pos.is_active and current_price is None,
            "is_active": pos.is_active,
            "exit_price": pos.exit_price,
            "exit_date": pos.exit_date.isoformat() if pos.exit_date else None,
            "realized_pnl": pos.realized_pnl,
            "exit_reason": pos.exit_reason,
            "invalidation_condition": pos.invalidation_condition,
        })

    logger.info(f"GET /portfolio/positions — {len(output)} pozisyon döndü (açık+kapalı 30g).")
    return output


# ─── Endpoint 2: GET /portfolio/history ────────────────────────────────────

@router.get("/portfolio/history")
async def get_history(
    days: int = Query(90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Son N günün snapshot geçmişi + benchmark + risk özeti."""
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
    benchmark_map = await _fetch_benchmark_history(days, db)

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
async def add_position(
    body: PositionCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    """
    Yeni pozisyon ekle + change_log'a ADD kaydı yaz.
    Sistem otomatik pozisyon açmaz — bu endpoint manuel çağrı içindir.
    """
    symbol = _normalize_symbol(body.symbol)
    _validate_positive_number(body.entry_price, "entry_price", required=True)
    _validate_positive_number(body.quantity, "quantity", required=True)
    _validate_positive_number(body.stop_loss, "stop_loss")
    _validate_positive_number(body.target_price, "target_price")
    await _ensure_active_stock(symbol, db)

    pos = PortfolioPosition(
        symbol=symbol,
        entry_price=body.entry_price,
        quantity=body.quantity,
        entry_date=body.entry_date,
        stop_loss=body.stop_loss,
        target_price=body.target_price,
        rationale=body.rationale,
        invalidation_condition=body.invalidation_condition,
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


# ─── Endpoint 4: PATCH /portfolio/positions/{id}/close ─────────────────────

@router.patch("/portfolio/positions/{position_id}/close")
async def close_position(
    position_id: int,
    body: PositionClose,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    """
    Açık pozisyonu kapat — is_active=False, exit_price/exit_date/realized_pnl yazar,
    change_log'a REMOVE kaydı ekler.
    """
    _validate_positive_number(body.exit_price, "exit_price", required=True)

    result = await db.execute(
        select(PortfolioPosition).where(
            PortfolioPosition.id == position_id,
            PortfolioPosition.is_active == True,  # noqa: E712
        )
    )
    pos = result.scalar_one_or_none()
    if pos is None:
        raise HTTPException(status_code=404, detail=f"Aktif pozisyon bulunamadı: id={position_id}")

    realized_pnl = round((body.exit_price - pos.entry_price) * pos.quantity, 4)

    pos.is_active = False
    pos.exit_price = body.exit_price
    pos.exit_date = body.exit_date
    pos.realized_pnl = realized_pnl
    pos.exit_reason = body.exit_reason

    log_entry = PortfolioChangeLog(
        date=datetime.now(timezone.utc).date(),
        action="REMOVE",
        symbol=pos.symbol,
        reason=f"Satış fiyatı: {body.exit_price}",
    )
    db.add(log_entry)
    await db.commit()

    logger.info(
        f"PATCH /portfolio/positions/{position_id}/close — {pos.symbol} kapatıldı "
        f"(realized_pnl={realized_pnl:.2f} TRY)."
    )
    return {
        "id": pos.id,
        "symbol": pos.symbol,
        "realized_pnl": realized_pnl,
        "status": "closed",
    }


# ─── Endpoint 5: GET /portfolio/analytics ──────────────────────────────────

@router.get("/portfolio/analytics")
async def get_portfolio_analytics(db: AsyncSession = Depends(get_db)):
    """
    PORT-01: Portföy betası (252 günlük, [0,3] kırpılmış, BIST100 benchmark).
    PORT-02: Pozisyonlar arası korelasyon matrisi (90 günlük).
    Aktif pozisyon yoksa beta=None, correlation_matrix=None döner.
    """
    # 1. Fetch active positions
    result = await db.execute(
        select(PortfolioPosition).where(PortfolioPosition.is_active == True)  # noqa: E712
    )
    positions = result.scalars().all()

    if not positions:
        return {
            "beta": None,
            "correlation_matrix": None,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
            "position_count": 0,
        }

    # 2. Resolve stock_id for each symbol
    symbols = list({p.symbol for p in positions})
    stock_result = await db.execute(
        select(Stock).where(Stock.symbol.in_(symbols), Stock.is_active == True)  # noqa: E712
    )
    stocks = stock_result.scalars().all()
    symbol_to_id = {s.symbol: s.id for s in stocks}

    if not symbol_to_id:
        return {
            "beta": None,
            "correlation_matrix": None,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
            "position_count": len(positions),
        }

    # 3. Fetch 252+ days of daily close prices per stock (beta window)
    beta_cutoff = date.today() - timedelta(days=252 + 10)

    price_result = await db.execute(
        select(PriceHistory)
        .where(
            PriceHistory.stock_id.in_(list(symbol_to_id.values())),
            PriceHistory.date >= beta_cutoff,
            PriceHistory.close.is_not(None),
        )
        .order_by(PriceHistory.stock_id, PriceHistory.date.asc())
    )
    price_rows = price_result.scalars().all()

    # Group closes by symbol
    id_to_symbol = {v: k for k, v in symbol_to_id.items()}
    closes_by_symbol: dict[str, list[tuple[str, float]]] = {sym: [] for sym in symbols}
    for row in price_rows:
        sym = id_to_symbol.get(row.stock_id)
        if sym:
            closes_by_symbol[sym].append((row.date.isoformat(), float(row.close)))

    # 4. Fetch benchmark (XU100.IS) for 252 days
    benchmark_map = await _fetch_benchmark_history(252, db)

    # 5. Compute portfolio beta
    beta_value = None
    # Build portfolio daily returns (value-weighted by entry_price * quantity)
    pos_by_symbol: dict[str, float] = {}
    for p in positions:
        pos_by_symbol[p.symbol] = pos_by_symbol.get(p.symbol, 0.0) + p.entry_price * p.quantity
    total_value = sum(pos_by_symbol.values()) or 1.0

    active_symbols = [sym for sym in symbols if sym in symbol_to_id]
    if active_symbols and benchmark_map:
        # Align dates across all symbols and benchmark
        all_dates_sets = [
            set(d for d, _ in closes_by_symbol[sym])
            for sym in active_symbols
            if closes_by_symbol[sym]
        ]
        benchmark_dates = set(benchmark_map.keys())
        if all_dates_sets and benchmark_dates:
            common_dates = sorted(
                all_dates_sets[0].intersection(*all_dates_sets[1:]).intersection(benchmark_dates)
            )
            if len(common_dates) >= 20:
                closes_dict_by_sym = {sym: dict(closes_by_symbol[sym]) for sym in active_symbols}
                port_closes = []
                bench_closes = []
                for d in common_dates:
                    port_close = sum(
                        closes_dict_by_sym[sym].get(d, 0.0) * (pos_by_symbol.get(sym, 0.0) / total_value)
                        for sym in active_symbols
                        if d in closes_dict_by_sym.get(sym, {})
                    )
                    port_closes.append(port_close)
                    bench_closes.append(benchmark_map[d])

                port_arr = np.array(port_closes, dtype=float)
                bench_arr = np.array(bench_closes, dtype=float)
                port_returns = np.diff(port_arr) / port_arr[:-1]
                bench_returns = np.diff(bench_arr) / bench_arr[:-1]

                # Remove NaN/inf
                mask = np.isfinite(port_returns) & np.isfinite(bench_returns)
                port_returns = port_returns[mask]
                bench_returns = bench_returns[mask]

                if len(port_returns) >= 10:
                    bench_var = float(np.var(bench_returns, ddof=1))
                    if bench_var > 1e-12:
                        cov = float(np.cov(port_returns, bench_returns)[0, 1])
                        raw_beta = cov / bench_var
                        beta_value = round(float(np.clip(raw_beta, 0.0, 3.0)), 4)

    # 6. Compute correlation matrix (90-day window)
    corr_cutoff = date.today() - timedelta(days=90 + 10)
    corr_cutoff_str = corr_cutoff.isoformat()
    included_symbols = []
    return_series: dict[str, np.ndarray] = {}

    for sym in active_symbols:
        recent_closes = [(d, c) for d, c in closes_by_symbol[sym] if d >= corr_cutoff_str]
        if len(recent_closes) < 20:
            continue
        recent_closes.sort(key=lambda x: x[0])
        close_arr = np.array([c for _, c in recent_closes], dtype=float)
        if len(close_arr) < 2:
            continue
        returns = np.diff(close_arr) / close_arr[:-1]
        valid = np.isfinite(returns)
        if valid.sum() < 20:
            continue
        return_series[sym] = returns[valid]
        included_symbols.append(sym)

    excluded_symbols = [s for s in active_symbols if s not in included_symbols]
    correlation_matrix = None

    if len(included_symbols) >= 2:
        # Align return series lengths (use minimum length)
        min_len = min(len(return_series[s]) for s in included_symbols)
        matrix_data = np.array([return_series[s][-min_len:] for s in included_symbols], dtype=float)
        corr = np.corrcoef(matrix_data)
        corr = np.clip(corr, -1.0, 1.0)
        correlation_matrix = {
            "symbols": included_symbols,
            "matrix": [[round(float(v), 4) for v in row] for row in corr.tolist()],
            "excluded_symbols": excluded_symbols,
        }
    elif len(included_symbols) == 1:
        correlation_matrix = {
            "symbols": included_symbols,
            "matrix": [[1.0]],
            "excluded_symbols": excluded_symbols,
        }

    logger.info(
        f"GET /portfolio/analytics — beta={beta_value}, "
        f"symbols={len(active_symbols)}, corr_included={len(included_symbols)}"
    )
    return {
        "beta": beta_value,
        "correlation_matrix": correlation_matrix,
        "calculated_at": datetime.now(timezone.utc).isoformat(),
        "position_count": len(positions),
    }

