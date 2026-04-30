"""Otomatik haftalık model portföy API router."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from app.core.security import verify_api_key

from app.services.model_portfolio import (
    generate_weekly_model_portfolio,
    get_current_model_portfolio,
    get_model_portfolio_history,
    take_model_portfolio_snapshot,
)

router = APIRouter()


@router.get("/model-portfolio/current")
async def model_portfolio_current():
    return await get_current_model_portfolio()


@router.get("/model-portfolio/history")
async def model_portfolio_history(limit: int = Query(12, ge=1, le=52)):
    return await get_model_portfolio_history(limit=limit)


@router.post("/model-portfolio/generate")
async def model_portfolio_generate(force: bool = Query(False), _: None = Depends(verify_api_key)):
    payload = await generate_weekly_model_portfolio(force=force)
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    return payload


@router.post("/model-portfolio/snapshot")
async def model_portfolio_snapshot(_: None = Depends(verify_api_key)):
    payload = await take_model_portfolio_snapshot()
    return {
        "snapshot": payload,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
