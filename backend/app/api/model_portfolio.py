"""Model portföy için frontend'in kullandığı endpoint'ler."""
from fastapi import APIRouter, Depends, Query

from app.core.security import verify_api_key
from app.services.model_portfolio import (
    generate_weekly_model_portfolio,
    get_current_model_portfolio,
    get_model_portfolio_history,
)

router = APIRouter()


@router.get("/model-portfolio/current")
async def model_portfolio_current():
    return await get_current_model_portfolio()


@router.get("/model-portfolio/history")
async def model_portfolio_history(limit: int = Query(12, ge=1, le=104)):
    return await get_model_portfolio_history(limit=limit)


@router.post("/model-portfolio/generate")
async def model_portfolio_generate(
    force: bool = Query(False),
    _: None = Depends(verify_api_key),
):
    return await generate_weekly_model_portfolio(force=force)
