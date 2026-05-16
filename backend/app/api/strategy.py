"""Strategy lab: backtests, risk guard, alerts and AI audit endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.ai_auditor import ai_auditor_service
from app.services.backtest import STRATEGIES, backtest_service
from app.services.risk_guard import risk_guard_service

router = APIRouter()


@router.get("/strategy/backtests")
async def run_backtest(
    strategy: str = Query("composite_signal"),
    years: int = Query(1, ge=1, le=3),
    symbols: str | None = Query(None, description="Virgulle ayrilmis semboller"),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Run a single strategy backtest for 1-3 years."""
    symbol_list = [item.strip().upper() for item in symbols.split(",") if item.strip()] if symbols else None
    try:
        return await backtest_service.run(db, strategy=strategy, years=years, symbols=symbol_list, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/strategy/backtests/compare")
async def compare_backtests(
    years: int = Query(1, ge=1, le=3),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Compare every built-in strategy over the same horizon."""
    return await backtest_service.compare_all(db, years=years, limit=limit)


@router.get("/strategy/backtests/strategies")
async def list_strategies():
    """List available backtest strategies."""
    return {
        "strategies": [
            {"key": spec.key, "label": spec.label, "description": spec.description}
            for spec in STRATEGIES.values()
        ]
    }


@router.get("/risk/portfolio")
async def get_portfolio_risk(
    portfolio_value: float = Query(100_000, ge=1_000, le=100_000_000),
    db: AsyncSession = Depends(get_db),
):
    """Portfolio risk guard: sector concentration, stop proximity and cash policy."""
    return await risk_guard_service.portfolio_risk(db, portfolio_value=portfolio_value)


@router.get("/alerts")
async def get_alerts(
    portfolio_value: float = Query(100_000, ge=1_000, le=100_000_000),
    db: AsyncSession = Depends(get_db),
):
    """Actionable alerts for stops, model deterioration, KAP flow and strong signals."""
    return await risk_guard_service.alerts(db, portfolio_value=portfolio_value)


@router.get("/ai/audit/{symbol}")
async def audit_stock(
    symbol: str,
    portfolio_value: float = Query(100_000, ge=1_000, le=100_000_000),
    risk_per_trade_pct: float = Query(1.0, ge=0.1, le=5.0),
    include_llm: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """AI auditor report for a concrete stock decision."""
    try:
        return await ai_auditor_service.audit_stock(
            db,
            symbol=symbol,
            portfolio_value=portfolio_value,
            risk_per_trade_pct=risk_per_trade_pct,
            include_llm=include_llm,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
