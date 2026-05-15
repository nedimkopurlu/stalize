"""Stock domain router — frontend'in kullandığı hisse verisi endpoint'leri."""
import math
import logging
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, Dict
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.news import NewsItem
from app.models.fundamental import Fundamental
from app.models.stock import Stock
from app.models.price import PriceHistory
from app.services.technical import technical_engine, compute_volume_ratio
from app.services.scoring import scoring_engine
from app.services.gemini_service import gemini_service
from app.services.investment_decision import DecisionInput, investment_decision_engine
from app.services.decision_guardrails import decision_guardrail_engine

router = APIRouter()
logger = logging.getLogger(__name__)


def _finite_or_none(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


def _list_data_quality_score(stock: Stock) -> float:
    score = 35.0
    if stock.is_bist30:
        score += 15
    elif stock.is_bist100:
        score += 10
    elif stock.is_bist250:
        score += 4
    score += sum(
        12
        for value in (stock.fundamental_score, stock.technical_score, stock.overall_score)
        if _finite_or_none(value) is not None
    )
    if _finite_or_none(stock.sentiment_score) is not None:
        score += 6
    last_data_update = getattr(stock, "last_data_update", None)
    if isinstance(last_data_update, datetime):
        last_update = last_data_update if last_data_update.tzinfo else last_data_update.replace(tzinfo=timezone.utc)
        age_hours = (datetime.now(timezone.utc) - last_update).total_seconds() / 3600
        if age_hours <= 12:
            score += 8
        elif age_hours > 48:
            score -= 8
    return round(max(0.0, min(100.0, score)), 2)


def _list_liquidity(stock: Stock, avg_volume: Optional[float]) -> dict:
    price = _finite_or_none(stock.current_price)
    volume = _finite_or_none(avg_volume) or _finite_or_none(stock.volume)
    traded_value = price * volume if price and volume else None
    thresholds = decision_guardrail_engine.thresholds
    if traded_value is None:
        score = 55.0
    elif traded_value >= thresholds.institutional_liquidity_traded_value:
        score = 95.0
    elif traded_value >= thresholds.high_liquidity_traded_value:
        score = 82.0
    elif traded_value >= thresholds.medium_liquidity_traded_value:
        score = 63.0
    elif traded_value >= thresholds.low_liquidity_traded_value:
        score = 42.0
    else:
        score = 22.0
    level = "high" if score >= 70 else "medium" if score >= 45 else "low"
    return {
        "score": round(score, 2),
        "level": level,
        "avg_traded_value": round(traded_value, 2) if traded_value is not None else None,
    }


@router.get("/stocks")
async def get_stocks(
    sort_by: str = Query("overall_score", description="Sıralama kriteri"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    sector: Optional[str] = None,
    bist30: Optional[bool] = None,
    bist100: Optional[bool] = None,
    bist250: Optional[bool] = None,
    search: Optional[str] = None,
    recommendation: Optional[str] = None,
    symbols: Optional[str] = Query(None, description="Virgülle ayrılmış sembol listesi: THYAO,GARAN,EREGL"),
    db: AsyncSession = Depends(get_db),
):
    """Hisse listesi — filtreleme ve sıralama. symbols parametresi ile sadece belirli hisseler döner."""
    query = select(Stock).where(Stock.is_active)

    if symbols:
        symbol_list = [s.strip().upper().removesuffix(".IS") for s in symbols.split(",") if s.strip()]
        if symbol_list:
            query = query.where(Stock.symbol.in_(symbol_list))
    else:
        symbol_list = []

    if bist30 is not None:
        if bist30:
            query = query.where(Stock.is_bist30)
    if bist100 is not None:
        if bist100:
            query = query.where(Stock.is_bist100 == True)
    if bist250 is not None:
        if bist250:
            query = query.where(Stock.is_bist250 == True)
    if sector:
        query = query.where(Stock.sector == sector)
    if search:
        query = query.where(
            (Stock.symbol.ilike(f"%{search}%")) | (Stock.name.ilike(f"%{search}%"))
        )
    if recommendation:
        query = query.where(Stock.recommendation == recommendation)

    # Sort
    sort_columns = {
        "symbol": Stock.symbol,
        "current_price": Stock.current_price,
        "daily_change_pct": Stock.daily_change_pct,
        "volume": Stock.volume,
        "market_cap": Stock.market_cap,
        "technical_score": Stock.technical_score,
        "fundamental_score": Stock.fundamental_score,
        "sentiment_score": Stock.sentiment_score,
        "overall_score": Stock.overall_score,
    }
    sort_col = sort_columns.get(sort_by, Stock.overall_score)
    if sort_col is not None:
        query = query.order_by(sort_col.desc().nullslast())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    stocks = result.scalars().all()

    # Batched 20-day average volume query (SGNL-02) — one subquery, no N+1
    from sqlalchemy import func as sa_func

    stock_ids = [s.id for s in stocks]
    avg_volumes: Dict[int, Optional[float]] = {sid: None for sid in stock_ids}

    if stock_ids:
        # Row-number window to get last 20 rows per stock, then group-average.
        row_num = sa_func.row_number().over(
            partition_by=PriceHistory.stock_id,
            order_by=PriceHistory.date.desc(),
        ).label("rn")
        ranked = (
            select(
                PriceHistory.stock_id.label("sid"),
                PriceHistory.volume.label("vol"),
                row_num,
            )
            .where(PriceHistory.stock_id.in_(stock_ids))
            .subquery()
        )
        avg_q = (
            select(ranked.c.sid, sa_func.avg(ranked.c.vol).label("avg_vol"))
            .where(ranked.c.rn <= 20)
            .group_by(ranked.c.sid)
        )
        avg_rows = await db.execute(avg_q)
        for sid, avg_vol in avg_rows.fetchall():
            avg_volumes[sid] = float(avg_vol) if avg_vol is not None else None

    # Total count
    count_query = select(func.count(Stock.id)).where(Stock.is_active)
    if symbol_list:
        count_query = count_query.where(Stock.symbol.in_(symbol_list))
    if bist30:
        count_query = count_query.where(Stock.is_bist30)
    if bist100:
        count_query = count_query.where(Stock.is_bist100 == True)
    if bist250:
        count_query = count_query.where(Stock.is_bist250 == True)
    if sector:
        count_query = count_query.where(Stock.sector == sector)
    if search:
        count_query = count_query.where(
            (Stock.symbol.ilike(f"%{search}%")) | (Stock.name.ilike(f"%{search}%"))
        )
    if recommendation:
        count_query = count_query.where(Stock.recommendation == recommendation)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    return {
        "stocks": [
            {
                "symbol": s.symbol, "name": s.name, "sector": s.sector,
                "industry": s.industry, "current_price": s.current_price,
                "daily_change_pct": s.daily_change_pct, "volume": s.volume,
                "volume_ratio": compute_volume_ratio(s.volume, avg_volumes.get(s.id)),
                "data_quality_score": s.data_quality_score,
                "liquidity_score": _list_liquidity(s, avg_volumes.get(s.id))["score"],
                "liquidity_level": _list_liquidity(s, avg_volumes.get(s.id))["level"],
                "avg_traded_value": _list_liquidity(s, avg_volumes.get(s.id))["avg_traded_value"],
                "market_cap": s.market_cap, "is_bist30": s.is_bist30,
                "is_bist100": s.is_bist100,
                "is_bist250": s.is_bist250,
                "market_tier": s.market_tier,
                "technical_score": s.technical_score,
                "fundamental_score": s.fundamental_score,
                "sentiment_score": s.sentiment_score,
                "overall_score": s.overall_score,
                "recommendation": s.recommendation,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            }
            for s in stocks
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/stocks/sectors")
async def get_stock_sectors(db: AsyncSession = Depends(get_db)):
    """Aktif hisselerin distinct sektör listesi — frontend dropdown için."""
    result = await db.execute(
        select(func.distinct(Stock.sector))
        .where(Stock.is_active)
        .where(Stock.sector.isnot(None))
        .order_by(Stock.sector)
    )
    sectors = [row[0] for row in result.fetchall()]
    return {"sectors": sectors}


@router.get("/stocks/kap-feed")
async def get_kap_feed(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Son KAP bildirimleri — source='KAP' olan NewsItem kayıtları."""
    result = await db.execute(
        select(NewsItem, Stock.symbol)
        .join(Stock, NewsItem.stock_id == Stock.id, isouter=True)
        .where(NewsItem.source == "KAP")
        .order_by(NewsItem.published_at.desc().nullslast(), NewsItem.id.desc())
        .limit(limit)
    )
    rows = result.fetchall()

    return [
        {
            "id": item.id,
            "symbol": sym or "",
            "title": item.title,
            "published_at": item.published_at.isoformat() if item.published_at else "",
            "kap_url": item.url,
        }
        for item, sym in rows
    ]


@router.get("/stocks/{symbol}/news")
async def get_stock_news(
    symbol: str,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Tek hisseye bağlı tüm güncel haber/KAP akışını döndürür."""
    stock_result = await db.execute(select(Stock).where(Stock.symbol == symbol.upper()))
    stock = stock_result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Hisse bulunamadı: {symbol}")

    news_result = await db.execute(
        select(NewsItem)
        .where(NewsItem.stock_id == stock.id)
        .order_by(NewsItem.published_at.desc().nullslast(), NewsItem.id.desc())
        .limit(limit)
    )
    items = news_result.scalars().all()

    return {
        "symbol": stock.symbol,
        "name": stock.name,
        "items": [
            {
                "id": item.id,
                "title": item.title,
                "summary": item.summary,
                "source": item.source,
                "category": item.category,
                "url": item.url,
                "published_at": item.published_at.isoformat() if item.published_at else None,
                "sentiment_score": item.sentiment_score,
                "sentiment_label": item.sentiment_label,
                "importance_score": item.importance_score,
            }
            for item in items
        ],
        "count": len(items),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/stocks/{symbol}")
async def get_stock_detail(
    symbol: str,
    db: AsyncSession = Depends(get_db),
):
    """Tek hisse detaylı bilgi."""
    result = await db.execute(
        select(Stock).where(Stock.symbol == symbol.upper())
    )
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Hisse bulunamadı: {symbol}")

    # Son 30 günlük fiyat
    prices_result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.stock_id == stock.id)
        .order_by(PriceHistory.date.desc())
        .limit(30)
    )
    recent_prices = prices_result.scalars().all()

    return {
        "stock": {
            "symbol": stock.symbol, "name": stock.name,
            "sector": stock.sector, "industry": stock.industry,
            "current_price": stock.current_price,
            "daily_change_pct": stock.daily_change_pct,
            "volume": stock.volume, "market_cap": stock.market_cap,
            "currency": stock.currency,
            "is_bist30": stock.is_bist30, "is_bist100": stock.is_bist100,
            "is_bist250": stock.is_bist250, "market_tier": stock.market_tier,
            "technical_score": stock.technical_score,
            "fundamental_score": stock.fundamental_score,
            "sentiment_score": stock.sentiment_score,
            "overall_score": stock.overall_score,
            "recommendation": stock.recommendation,
            "data_quality_score": stock.data_quality_score,
            "last_data_update": stock.last_data_update.isoformat() if stock.last_data_update else None,
        },
        "recent_prices": [
            {
                "date": p.date.isoformat(),
                "open": p.open, "high": p.high, "low": p.low,
                "close": p.close, "volume": p.volume,
                "sma_20": p.sma_20, "sma_50": p.sma_50, "sma_200": p.sma_200,
                "rsi_14": p.rsi_14, "macd": p.macd, "macd_signal": p.macd_signal,
                "bb_upper": p.bb_upper, "bb_middle": p.bb_middle, "bb_lower": p.bb_lower,
            }
            for p in reversed(recent_prices)
        ],
    }


@router.get("/stocks/{symbol}/prices")
async def get_stock_prices(
    symbol: str,
    period: str = Query("1y", description="1m, 3m, 6m, 1y, 5y"),
    db: AsyncSession = Depends(get_db),
):
    """Hisse fiyat geçmişi — grafik verisi."""
    result = await db.execute(
        select(Stock).where(Stock.symbol == symbol.upper())
    )
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Hisse bulunamadı: {symbol}")

    # Period mapping
    period_days = {"1d": 1, "1wk": 7, "1m": 30, "3m": 90, "6m": 180, "1y": 365, "5y": 1825}
    days = period_days.get(period, 365)
    start_date = datetime.now(timezone.utc).date() - timedelta(days=days)

    prices_result = await db.execute(
        select(PriceHistory)
        .where(and_(
            PriceHistory.stock_id == stock.id,
            PriceHistory.date >= start_date,
        ))
        .order_by(PriceHistory.date.asc())
    )
    prices = prices_result.scalars().all()

    return {
        "symbol": stock.symbol,
        "name": stock.name,
        "period": period,
        "prices": [
            {
                "date": p.date.isoformat(),
                "open": p.open, "high": p.high, "low": p.low,
                "close": p.close, "volume": p.volume,
                "sma_20": p.sma_20, "sma_50": p.sma_50, "sma_200": p.sma_200,
                "ema_12": p.ema_12, "ema_26": p.ema_26,
                "rsi_14": p.rsi_14,
                "macd": p.macd, "macd_signal": p.macd_signal, "macd_histogram": p.macd_histogram,
                "bb_upper": p.bb_upper, "bb_middle": p.bb_middle, "bb_lower": p.bb_lower,
                "atr_14": p.atr_14, "obv": p.obv,
            }
            for p in prices
        ],
    }


@router.get("/stocks/{symbol}/technical")
async def get_stock_technical(symbol: str, db: AsyncSession = Depends(get_db)):
    """Tek hisse için tam teknik analiz."""
    result = await technical_engine.analyze_stock(symbol.upper())
    if not result:
        stock_result = await db.execute(select(Stock).where(Stock.symbol == symbol.upper()))
        stock = stock_result.scalar_one_or_none()
        if not stock:
            raise HTTPException(status_code=404, detail=f"Hisse bulunamadı: {symbol}")
        current = stock.current_price
        result = {
            "symbol": stock.symbol,
            "score": stock.technical_score if stock.technical_score is not None else 50.0,
            "recommendation": stock.recommendation or "TUT",
            "signals": [],
            "support": None,
            "resistance": None,
            "stop_loss": round(current * 0.92, 2) if current else None,
            "target_price": round(current * 1.12, 2) if current else None,
            "indicators": {
                "last_close": current,
                "rsi_14": None,
                "macd": None,
                "macd_signal": None,
                "adx": None,
                "bb_width": None,
                "sma_50": None,
                "sma_200": None,
                "ema_trend_score": 50.0,
            },
            "ema_50": [],
            "ema_200": [],
            "status": "insufficient_history",
        }
    return result


@router.get("/stocks/{symbol}/score-breakdown")
async def get_stock_score_breakdown(
    symbol: str,
    db: AsyncSession = Depends(get_db),
):
    """Tek hissenin skor katkı kırılımını getir."""
    result = await db.execute(
        select(Stock).where(Stock.symbol == symbol.upper())
    )
    stock = result.scalar_one_or_none()

    if not stock:
        raise HTTPException(status_code=404, detail=f"Hisse bulunamadı: {symbol}")

    prices_result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.stock_id == stock.id)
        .order_by(PriceHistory.date.desc())
        .limit(260)
    )
    prices = list(prices_result.scalars().all())
    market_regime = await decision_guardrail_engine.market_regime(db)
    guardrails = decision_guardrail_engine.evaluate(stock, prices, market_regime=market_regime)

    breakdown = await scoring_engine.get_contextual_score_breakdown(stock, db=db)
    guardrail_components = [
        {
            "key": "data_quality",
            "label": "Veri Güveni",
            "raw_score": guardrails["data_quality"]["score"],
            "base_weight": 0.0,
            "normalized_weight": 0.0,
            "contribution": 0.0,
            "reason": guardrails["data_quality"]["source_caveat"],
        },
        {
            "key": "liquidity",
            "label": "Likidite",
            "raw_score": guardrails["liquidity"]["score"],
            "base_weight": 0.0,
            "normalized_weight": 0.0,
            "contribution": 0.0,
            "reason": "Ortalama işlem hacmi ve işlem yapılabilirlik kontrolü.",
        },
        {
            "key": "limit_lock",
            "label": "Tavan/Taban",
            "raw_score": 100.0 if guardrails["limit_lock"]["status"] == "clear" else 35.0,
            "base_weight": 0.0,
            "normalized_weight": 0.0,
            "contribution": 0.0,
            "reason": guardrails["limit_lock"]["warning"] or "Son günlerde tavan/taban benzeri hareket saptanmadı.",
        },
    ]
    breakdown["components"].extend(guardrail_components)
    breakdown["summary"]["available_component_count"] += len(guardrail_components)
    return {
        "symbol": stock.symbol,
        "name": stock.name,
        "breakdown": breakdown,
        "guardrails": guardrails,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/stocks/{symbol}/decision")
async def get_stock_decision(
    symbol: str,
    portfolio_value: float = Query(100_000, ge=1_000, le=100_000_000),
    risk_per_trade_pct: float = Query(1.0, ge=0.1, le=5.0),
    calibrated: bool = Query(False, description="Ölçülmüş sinyal sonuçlarından önerilen policy uygulansın mı?"),
    db: AsyncSession = Depends(get_db),
):
    """Risk kontrollü işlem kararı: eylem, giriş bölgesi, stop, hedef ve pozisyon büyüklüğü."""
    result = await db.execute(select(Stock).where(Stock.symbol == symbol.upper()))
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Hisse bulunamadı: {symbol}")

    prices_result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.stock_id == stock.id)
        .order_by(PriceHistory.date.desc())
        .limit(260)
    )
    prices = list(prices_result.scalars().all())
    if not prices and not stock.current_price:
        raise HTTPException(status_code=503, detail=f"{symbol} için fiyat verisi yok")

    policy = None
    if calibrated:
        from app.services.signal_tracking import signal_tracking_service

        report = await signal_tracking_service.calibration_report(db, horizon="1w", min_count=1)
        policy = signal_tracking_service.policy_from_report(report)

    market_regime = await decision_guardrail_engine.market_regime(db)
    decision = investment_decision_engine.build_decision(
        DecisionInput(
            stock=stock,
            prices=prices,
            portfolio_value=portfolio_value,
            risk_per_trade_pct=risk_per_trade_pct,
            policy=policy,
            market_regime=market_regime,
        )
    )
    decision["generated_at"] = datetime.now(timezone.utc).isoformat()
    return decision


@router.get("/signals/top")
async def get_top_signals(
    limit: int = Query(20, ge=1, le=100),
    portfolio_value: float = Query(100_000, ge=1_000, le=100_000_000),
    risk_per_trade_pct: float = Query(1.0, ge=0.1, le=5.0),
    calibrated: bool = Query(False, description="Ölçülmüş sonuçlardan önerilen policy uygulansın mı?"),
    db: AsyncSession = Depends(get_db),
):
    """Tüm aktif hisselerden en güçlü risk-ayarlı kararları döndürür."""
    stock_result = await db.execute(
        select(Stock)
        .where(Stock.is_active, Stock.current_price.isnot(None))
        .order_by(Stock.overall_score.desc().nullslast())
        .limit(200)
    )
    stocks = list(stock_result.scalars().all())
    if not stocks:
        return {"signals": [], "count": 0, "generated_at": datetime.now(timezone.utc).isoformat()}

    stock_ids = [s.id for s in stocks]
    price_result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.stock_id.in_(stock_ids))
        .order_by(PriceHistory.stock_id.asc(), PriceHistory.date.desc())
    )
    prices_by_stock: dict[int, list[PriceHistory]] = {sid: [] for sid in stock_ids}
    for price in price_result.scalars().all():
        bucket = prices_by_stock.get(price.stock_id)
        if bucket is not None and len(bucket) < 260:
            bucket.append(price)

    decisions = []
    policy = None
    if calibrated:
        from app.services.signal_tracking import signal_tracking_service

        report = await signal_tracking_service.calibration_report(db, horizon="1w", min_count=1)
        policy = signal_tracking_service.policy_from_report(report)

    market_regime = await decision_guardrail_engine.market_regime(db)

    for stock in stocks:
        try:
            decisions.append(
                investment_decision_engine.build_decision(
                    DecisionInput(
                        stock=stock,
                        prices=prices_by_stock.get(stock.id, []),
                        portfolio_value=portfolio_value,
                        risk_per_trade_pct=risk_per_trade_pct,
                        policy=policy,
                        market_regime=market_regime,
                    )
                )
            )
        except ValueError:
            continue

    ranked = investment_decision_engine.rank_decisions(decisions)[:limit]
    return {
        "signals": ranked,
        "count": len(ranked),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/stocks/{symbol}/fundamentals")
async def get_stock_fundamentals(
    symbol: str,
    db: AsyncSession = Depends(get_db),
):
    """Hisse için en güncel temel analiz verileri."""
    stock_result = await db.execute(
        select(Stock).where(Stock.symbol == symbol.upper())
    )
    stock = stock_result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Hisse bulunamadı: {symbol}")

    # En son period kaydını al (updated_at desc)
    fund_result = await db.execute(
        select(Fundamental)
        .where(Fundamental.stock_id == stock.id)
        .order_by(Fundamental.updated_at.desc())
        .limit(1)
    )
    fund = fund_result.scalar_one_or_none()

    if not fund:
        return {
            "symbol": stock.symbol,
            "period": "vendor-data-missing",
            "pe_ratio": None,
            "pb_ratio": None,
            "roe": None,
            "net_margin": None,
            "debt_to_equity": None,
            "fundamental_score": stock.fundamental_score if stock.fundamental_score is not None else 50.0,
            "ev_ebitda": None,
            "data_quality": "neutral_fallback",
        }

    return {
        "symbol": stock.symbol,
        "period": fund.period,
        "pe_ratio": _finite_or_none(fund.pe_ratio),
        "pb_ratio": _finite_or_none(fund.pb_ratio),
        "roe": _finite_or_none(fund.roe),
        "net_margin": _finite_or_none(fund.net_margin),
        "debt_to_equity": _finite_or_none(fund.debt_to_equity),
        "fundamental_score": _finite_or_none(fund.fundamental_score),
        "ev_ebitda": _finite_or_none(fund.ev_ebitda),
    }


@router.get("/stocks/{symbol}/peers")
async def get_stock_peers(
    symbol: str,
    db: AsyncSession = Depends(get_db),
):
    """Aynı sektörden 3-5 hisse döndürür (rakip karşılaştırma)."""
    # Get the target stock
    result = await db.execute(select(Stock).where(Stock.symbol == symbol.upper()))
    stock = result.scalar_one_or_none()
    if not stock or not stock.sector:
        return {"peers": []}

    # Get same-sector stocks, exclude self, limit to 5
    peers_result = await db.execute(
        select(Stock)
        .where(
            and_(
                Stock.sector == stock.sector,
                Stock.symbol != stock.symbol,
                Stock.is_active == True,
                Stock.current_price.isnot(None),
            )
        )
        .order_by(Stock.market_cap.desc().nullslast())
        .limit(5)
    )
    peers = peers_result.scalars().all()

    return {
        "symbol": stock.symbol,
        "sector": stock.sector,
        "peers": [
            {
                "symbol": p.symbol,
                "name": p.name,
                "current_price": p.current_price,
                "daily_change_pct": p.daily_change_pct,
                "market_cap": p.market_cap,
                "overall_score": p.overall_score,
                "recommendation": p.recommendation,
                "is_bist30": p.is_bist30,
                "is_bist100": p.is_bist100,
            }
            for p in peers
        ],
    }


@router.post("/stocks/{symbol}/analyze")
async def analyze_stock(
    symbol: str,
    db: AsyncSession = Depends(get_db),
):
    """On-demand OpenAI Türkçe hisse analizi üretir. Önbellek frontend sorumluluğundadır."""
    result = await db.execute(select(Stock).where(Stock.symbol == symbol.upper()))
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail=f"{symbol} bulunamadı.")

    # En güncel temel analiz verisini al
    fund_result = await db.execute(
        select(Fundamental)
        .where(Fundamental.stock_id == stock.id)
        .order_by(Fundamental.updated_at.desc())
        .limit(1)
    )
    fund = fund_result.scalar_one_or_none()

    prices_result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.stock_id == stock.id)
        .order_by(PriceHistory.date.desc())
        .limit(260)
    )
    prices = list(prices_result.scalars().all())
    latest_price = sorted(prices, key=lambda p: p.date)[-1] if prices else None

    decision = None
    try:
        market_regime = await decision_guardrail_engine.market_regime(db)
        decision = investment_decision_engine.build_decision(
            DecisionInput(
                stock=stock,
                prices=prices,
                portfolio_value=100_000,
                risk_per_trade_pct=1,
                market_regime=market_regime,
            )
        )
    except ValueError:
        decision = None

    news_result = await db.execute(
        select(NewsItem)
        .where(NewsItem.stock_id == stock.id)
        .order_by(NewsItem.published_at.desc().nullslast(), NewsItem.id.desc())
        .limit(12)
    )
    news_items = news_result.scalars().all()

    fund_pe = _finite_or_none(fund.pe_ratio) if fund else None
    fund_pb = _finite_or_none(fund.pb_ratio) if fund else None
    fund_ev_ebitda = _finite_or_none(fund.ev_ebitda) if fund else None
    fund_roe = _finite_or_none(fund.roe) if fund else None
    fund_roa = _finite_or_none(fund.roa) if fund else None
    fund_net_margin = _finite_or_none(fund.net_margin) if fund else None
    fund_gross_margin = _finite_or_none(fund.gross_margin) if fund else None
    fund_revenue_growth = _finite_or_none(fund.revenue_growth_yoy) if fund else None
    fund_earnings_growth = _finite_or_none(fund.earnings_growth_yoy) if fund else None
    fund_market_cap = _finite_or_none(fund.market_cap) if fund else None
    fund_dividend_yield = _finite_or_none(fund.dividend_yield) if fund else None
    fund_debt_equity = _finite_or_none(fund.debt_to_equity) if fund else None

    pe = f"{fund_pe:.1f}" if fund_pe is not None else None
    pb = f"{fund_pb:.2f}" if fund_pb is not None else None
    ev_ebitda = f"{fund_ev_ebitda:.1f}" if fund_ev_ebitda is not None else None
    roe = f"{fund_roe * 100:.1f}%" if fund_roe is not None else None
    roa = f"{fund_roa * 100:.1f}%" if fund_roa is not None else None
    net_margin = f"{fund_net_margin * 100:.1f}%" if fund_net_margin is not None else None
    gross_margin = f"{fund_gross_margin * 100:.1f}%" if fund_gross_margin is not None else None
    revenue_growth = f"{fund_revenue_growth * 100:.1f}%" if fund_revenue_growth is not None else None
    earnings_growth = f"{fund_earnings_growth * 100:.1f}%" if fund_earnings_growth is not None else None
    market_cap = fund_market_cap if fund_market_cap is not None else _finite_or_none(stock.market_cap)
    dividend_yield = f"{fund_dividend_yield * 100:.2f}%" if fund_dividend_yield is not None else None
    debt_equity = f"{fund_debt_equity:.2f}" if fund_debt_equity is not None else None

    # Fiyat ve teknik bilgiler
    price = f"{stock.current_price:.2f} TL" if stock.current_price else "bilinmiyor"
    change = (f"%+.2f" % stock.daily_change_pct) if stock.daily_change_pct is not None else "bilinmiyor"
    score = f"{stock.overall_score:.1f}/100" if stock.overall_score is not None else "bilinmiyor"
    rec = stock.recommendation or "bilinmiyor"
    sector = stock.sector or "bilinmiyor"
    name = stock.name or stock.symbol

    # Temel analiz satırları — sadece mevcut veriler
    fund_lines = []
    if pe:      fund_lines.append(f"  - F/K oranı: {pe} (sektör ortalamasıyla kıyasla)")
    if pb:      fund_lines.append(f"  - PD/DD oranı: {pb}")
    if ev_ebitda: fund_lines.append(f"  - FD/FAVÖK oranı: {ev_ebitda}")
    if roe:     fund_lines.append(f"  - Öz sermaye getirisi (ROE): {roe}")
    if roa:     fund_lines.append(f"  - Aktif kârlılığı (ROA): {roa}")
    if net_margin: fund_lines.append(f"  - Net kâr marjı: {net_margin}")
    if gross_margin: fund_lines.append(f"  - Brüt kâr marjı: {gross_margin}")
    if revenue_growth: fund_lines.append(f"  - Yıllık gelir büyümesi: {revenue_growth}")
    if earnings_growth: fund_lines.append(f"  - Yıllık kâr büyümesi: {earnings_growth}")
    if dividend_yield: fund_lines.append(f"  - Temettü verimi: {dividend_yield}")
    if debt_equity:    fund_lines.append(f"  - Borç/Öz Sermaye: {debt_equity}")
    if market_cap:
        mc_b = market_cap / 1e9
        fund_lines.append(f"  - Piyasa değeri: {mc_b:.1f} Milyar TL")

    fund_section = "\n".join(fund_lines) if fund_lines else "  - Temel veriler mevcut değil"

    technical_lines = []
    if latest_price:
        if latest_price.rsi_14 is not None:
            technical_lines.append(f"  - RSI(14): {latest_price.rsi_14:.1f}")
        if latest_price.macd is not None and latest_price.macd_signal is not None:
            technical_lines.append(f"  - MACD / Sinyal: {latest_price.macd:.2f} / {latest_price.macd_signal:.2f}")
        if latest_price.sma_50 is not None:
            technical_lines.append(f"  - SMA 50: {latest_price.sma_50:.2f} TL")
        if latest_price.sma_200 is not None:
            technical_lines.append(f"  - SMA 200: {latest_price.sma_200:.2f} TL")
        if latest_price.atr_14 is not None:
            technical_lines.append(f"  - ATR(14): {latest_price.atr_14:.2f}")
    technical_section = "\n".join(technical_lines) if technical_lines else "  - Teknik indikatör verileri sınırlı"

    if decision:
        entry = decision["entry_zone"]
        guardrails = decision.get("guardrails", {})
        checklist = guardrails.get("pre_trade_checklist", [])
        guardrail_lines = [
            f"  - {item.get('label')}: {item.get('status')} — {item.get('detail')}"
            for item in checklist
        ]
        guardrail_section = "\n".join(guardrail_lines) if guardrail_lines else "  - Guardrail verisi yok"
        decision_section = f"""  - Karar: {decision["action_label"]} ({decision["confidence"]}/100 güven)
  - Zaman ufku: 2-8 hafta
  - Giriş bölgesi: {entry["low"]:.2f} - {entry["high"]:.2f} TL
  - Stop: {decision["stop_loss"]:.2f} TL
  - Hedef: {decision["target_price"]:.2f} TL
  - Risk/Ödül: {decision["risk_reward"]:.2f}
  - Pozisyon: {decision["position_size"]["shares"]} adet, yaklaşık %{decision["position_size"]["estimated_exposure_pct"]:.2f} portföy"""
    else:
        decision_section = "  - Karar motoru için yeterli fiyat verisi yok"
        guardrail_section = "  - Guardrail verisi yok"

    news_lines = []
    for item in news_items:
        published = item.published_at.date().isoformat() if item.published_at else "tarih yok"
        source = item.source or "kaynak yok"
        sentiment = item.sentiment_label or "nötr"
        news_lines.append(f"  - {published} · {source} · {sentiment}: {item.title}")
    news_section = "\n".join(news_lines) if news_lines else "  - Bu hisseye bağlı güncel haber kaydı yok"

    prompt = f"""Aşağıdaki verilere dayanarak {name} ({stock.symbol}) hissesi için kapsamlı, karar odaklı bir yatırım analizi yaz.

## Hisse Verileri
- Sektör: {sector}
- Güncel Fiyat: {price}
- Günlük Değişim: {change}
- Model Skoru: {score}
- Sistem Önerisi: {rec}
- Teknik Skor: {stock.technical_score if stock.technical_score is not None else "bilinmiyor"}
- Temel Skor: {stock.fundamental_score if stock.fundamental_score is not None else "bilinmiyor"}
- Haber/Sentiment Skoru: {stock.sentiment_score if stock.sentiment_score is not None else "bilinmiyor"}

## İşlem Planı
{decision_section}

## İşlem Öncesi Guardrail Kontrolleri
{guardrail_section}

## Teknik Analiz Verileri
{technical_section}

## Temel Analiz Verileri
{fund_section}

## Haber ve KAP Akışı
{news_section}

## Analiz Talimatları
1. İlk satırda direkt emir verme; "Yüksek Öncelikli İzleme / Pozitif Görünüm / Nötr İzleme / Riskli Görünüm" dilini kullan.
2. Guardrail kontrollerinden block/warning varsa pozitif dili mutlaka düşür ve nedenini açıkça yaz.
3. "Neden takip ederim?" bölümünde teknik, temel ve haber kanıtlarını birleştir.
4. "Neden vazgeçerim?" bölümünde bu işlemin hangi senaryoda ters gideceğini yaz.
5. Teknik analizde trend, momentum, destek/direnç, stop ve hedefi ayrı ayrı yorumla.
6. Temel analizde değerleme, kârlılık, büyüme, bilanço kalitesi ve borç riskini yorumla.
7. Haber/KAP tarafında olumlu/olumsuz etkileri ve takip edilmesi gereken başlıkları özetle.
8. Son bölümde giriş bölgesi, stop, hedef, risk/ödül ve pozisyon büyüklüğünü uygulanabilir şekilde yaz.
9. Temel veriler resmi KAP finansallarıyla doğrulanmamışsa bunu güven notunda belirt.

Türkçe yaz. Kısa ama yoğun olsun. Başlıklar kullan; gereksiz genel piyasa lafı ekleme. Veride yoksa açıkça "veri yok" de."""

    analysis_text = await gemini_service.generate(prompt)

    return {
        "symbol": stock.symbol,
        "analysis": analysis_text,
        "cached": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
