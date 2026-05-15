"""Signal tracking endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.signal_tracking import signal_tracking_service

router = APIRouter()


@router.post("/signals/snapshots/run")
async def run_signal_snapshot(
    limit: int = Query(40, ge=1, le=100),
    portfolio_value: float = Query(100_000, ge=1_000, le=100_000_000),
    risk_per_trade_pct: float = Query(1.0, ge=0.1, le=5.0),
    db: AsyncSession = Depends(get_db),
):
    """Persist today's strongest signal decisions for future measurement."""
    return await signal_tracking_service.snapshot_top_signals(
        db,
        limit=limit,
        portfolio_value=portfolio_value,
        risk_per_trade_pct=risk_per_trade_pct,
    )


@router.post("/signals/outcomes/evaluate")
async def evaluate_signal_outcomes(db: AsyncSession = Depends(get_db)):
    """Evaluate matured signal snapshots against realized stock and BIST100 returns."""
    return await signal_tracking_service.evaluate_outcomes(db)


@router.get("/signals/outcomes")
async def get_signal_outcomes(
    limit: int = Query(50, ge=1, le=200),
    action: Optional[str] = Query(None),
    outcome: Optional[str] = Query(None),
    horizon: str = Query("1w", pattern="^(1w|1m)$"),
    regime: Optional[str] = Query(None, description="Piyasa rejimi filtresi (Boğa/Ayı/Yatay/Volatil)"),
    db: AsyncSession = Depends(get_db),
):
    """List persisted signal decisions with 1-week or 1-month outcome fields."""
    return await signal_tracking_service.list_outcomes(
        db,
        limit=limit,
        action=action,
        outcome=outcome,
        horizon=horizon,
        regime=regime,
    )


@router.get("/signals/calibration")
async def get_signal_calibration(
    horizon: str = Query("1w", pattern="^(1w|1m)$"),
    min_count: int = Query(1, ge=1, le=50),
    regime: Optional[str] = Query(None, description="Piyasa rejimi filtresi (Boğa/Ayı/Yatay/Volatil)"),
    db: AsyncSession = Depends(get_db),
):
    """Summarize which signal groups are working by action, risk, and sector."""
    return await signal_tracking_service.calibration_report(
        db,
        horizon=horizon,
        min_count=min_count,
        regime=regime,
    )
