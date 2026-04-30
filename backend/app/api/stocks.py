"""Stock domain router — hisse listesi, detay, fiyat, teknik analiz, sıralama, skorlama."""
import logging
from fastapi import APIRouter, HTTPException, Query, Depends
from app.core.security import verify_api_key
from typing import Optional, List, Dict
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.news import NewsItem
from app.models.fundamental import Fundamental
from app.models.stock import Stock
from app.models.price import CommodityPrice, PriceHistory
from app.services.data_collector import get_yahoo_chart_history
from app.services.technical import technical_engine, compute_volume_ratio
from app.services.scoring import scoring_engine

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/stocks")
async def get_stocks(
    sort_by: str = Query("overall_score", description="Sıralama kriteri"),
    limit: int = Query(100, ge=1, le=200),
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
                "market_cap": s.market_cap, "is_bist30": s.is_bist30,
                "is_bist100": s.is_bist100,
                "technical_score": s.technical_score,
                "fundamental_score": s.fundamental_score,
                "sentiment_score": s.sentiment_score,
                "overall_score": s.overall_score,
                "recommendation": s.recommendation,
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


@router.get("/stocks/sparkline")
async def get_sparkline(
    symbol: str = Query(..., description="yfinance sembolü, örn. XU100 veya USDTRY=X"),
    days: int = Query(30, ge=5, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Son N günlük kapanış verisi — dashboard sparkline grafiği için."""
    from datetime import date as date_cls

    end = date_cls.today()
    start = end - timedelta(days=days + 7)  # yfinance hafta sonu/tatil boşluklarını kapsar
    market_symbol = "XU100.IS" if symbol.upper() == "XU100" else symbol

    db_rows = await db.execute(
        select(CommodityPrice)
        .where(CommodityPrice.symbol == market_symbol, CommodityPrice.date >= start)
        .order_by(CommodityPrice.date.asc())
    )
    points = [
        {"date": row.date.isoformat(), "close": float(row.close)}
        for row in db_rows.scalars().all()
        if row.close is not None
    ]
    if points:
        return {"symbol": symbol, "points": points[-days:]}

    fallback_period = "1mo" if days <= 30 else "3mo" if days <= 90 else "1y"
    df = await get_yahoo_chart_history(market_symbol, period=fallback_period)

    if df is None or df.empty:
        return {"symbol": symbol, "points": []}

    points = []
    for idx, row in df.iterrows():
        close_val = row.get("Close", None)
        if close_val is None:
            continue
        try:
            close_float = float(close_val)
        except (TypeError, ValueError):
            continue
        date_str = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
        points.append({"date": date_str, "close": close_float})

    # Son `days` noktayı al
    points = points[-days:]
    return {"symbol": symbol, "points": points}


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
            "technical_score": stock.technical_score,
            "fundamental_score": stock.fundamental_score,
            "sentiment_score": stock.sentiment_score,
            "overall_score": stock.overall_score,
            "recommendation": stock.recommendation,
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
    period_days = {"1m": 30, "3m": 90, "6m": 180, "1y": 365, "5y": 1825}
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
async def get_stock_technical(symbol: str):
    """Tek hisse için tam teknik analiz."""
    result = await technical_engine.analyze_stock(symbol.upper())
    if not result:
        raise HTTPException(status_code=404, detail=f"Teknik analiz yapılamadı: {symbol}")
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

    breakdown = await scoring_engine.get_contextual_score_breakdown(stock)
    return {
        "symbol": stock.symbol,
        "name": stock.name,
        "breakdown": breakdown,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/stocks/{symbol}/news")
async def get_stock_news(
    symbol: str,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Tek hisse için son haber/KAP akışını getir."""
    stock_result = await db.execute(
        select(Stock).where(Stock.symbol == symbol.upper())
    )
    stock = stock_result.scalar_one_or_none()

    if not stock:
        raise HTTPException(status_code=404, detail=f"Hisse bulunamadı: {symbol}")

    news_result = await db.execute(
        select(NewsItem)
        .where(NewsItem.stock_id == stock.id)
        .order_by(NewsItem.published_at.desc(), NewsItem.id.desc())
        .limit(limit)
    )
    news_items = news_result.scalars().all()

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
            for item in news_items
        ],
        "count": len(news_items),
        "timestamp": datetime.now(timezone.utc).isoformat(),
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
            "period": None,
            "pe_ratio": None,
            "pb_ratio": None,
            "roe": None,
            "net_margin": None,
            "debt_to_equity": None,
            "fundamental_score": None,
            "ev_ebitda": None,
        }

    return {
        "symbol": stock.symbol,
        "period": fund.period,
        "pe_ratio": fund.pe_ratio,
        "pb_ratio": fund.pb_ratio,
        "roe": fund.roe,
        "net_margin": fund.net_margin,
        "debt_to_equity": fund.debt_to_equity,
        "fundamental_score": fund.fundamental_score,
        "ev_ebitda": fund.ev_ebitda,
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


@router.post("/analysis/technical/run")
async def run_technical_analysis(_: None = Depends(verify_api_key)):
    """Tüm hisseler için teknik analiz çalıştır."""
    results = await technical_engine.analyze_all()
    return {
        "status": "completed",
        "analyzed": len(results),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/rankings")
async def get_rankings(
    sort_by: str = Query("overall_score"),
    limit: int = Query(30, ge=1, le=100),
    sector: Optional[str] = None,
    bist30: bool = Query(False),
):
    """Hisse sıralaması."""
    results = await scoring_engine.get_rankings(
        sort_by=sort_by, limit=limit,
        sector=sector, bist30_only=bist30,
    )
    return {"rankings": results, "sort_by": sort_by, "count": len(results)}


@router.get("/sectors")
async def get_sectors(db: AsyncSession = Depends(get_db)):
    """Sektör bazlı özet."""
    result = await db.execute(
        select(
            Stock.sector,
            func.count(Stock.id).label("count"),
            func.avg(Stock.overall_score).label("avg_score"),
            func.avg(Stock.daily_change_pct).label("avg_change"),
        )
        .where(and_(Stock.is_active, Stock.sector.isnot(None)))
        .group_by(Stock.sector)
        .order_by(func.avg(Stock.overall_score).desc().nullslast())
    )
    sectors = result.fetchall()

    return {
        "sectors": [
            {
                "sector": s[0],
                "stock_count": s[1],
                "avg_score": round(float(s[2]), 2) if s[2] else None,
                "avg_daily_change": round(float(s[3]), 2) if s[3] else None,
            }
            for s in sectors
        ]
    }


@router.post("/scoring/update")
async def update_all_scores(_: None = Depends(verify_api_key)):
    """Tüm hisse skorlarını güncelle."""
    updated = await scoring_engine.update_all_scores()
    return {"status": "completed", "updated": updated}


@router.get("/screener")
async def screen_stocks(
    # Sector & index filters
    sector: Optional[str] = None,
    bist30: Optional[bool] = None,
    bist100: Optional[bool] = None,
    bist250: Optional[bool] = None,
    # Score filters
    score_min: Optional[float] = None,
    score_max: Optional[float] = None,
    recommendation: Optional[str] = None,
    # Price/market filters
    market_cap_min: Optional[float] = None,
    market_cap_max: Optional[float] = None,
    daily_change_min: Optional[float] = None,
    daily_change_max: Optional[float] = None,
    # Fundamental filters
    pe_ratio_min: Optional[float] = None,
    pe_ratio_max: Optional[float] = None,
    pb_ratio_min: Optional[float] = None,
    pb_ratio_max: Optional[float] = None,
    roe_min: Optional[float] = None,
    roe_max: Optional[float] = None,
    debt_to_equity_max: Optional[float] = None,
    # Pagination
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("overall_score"),
    db: AsyncSession = Depends(get_db),
):
    """Çok boyutlu hisse tarama motoru."""
    # Validate range params — min > max yields no results and is likely a client mistake
    range_pairs = [
        ("pe_ratio_min", pe_ratio_min, "pe_ratio_max", pe_ratio_max),
        ("pb_ratio_min", pb_ratio_min, "pb_ratio_max", pb_ratio_max),
        ("roe_min", roe_min, "roe_max", roe_max),
        ("score_min", score_min, "score_max", score_max),
        ("market_cap_min", market_cap_min, "market_cap_max", market_cap_max),
        ("daily_change_min", daily_change_min, "daily_change_max", daily_change_max),
    ]
    for min_name, min_val, max_name, max_val in range_pairs:
        if min_val is not None and max_val is not None and min_val > max_val:
            raise HTTPException(
                status_code=400,
                detail=f"{min_name} ({min_val}) cannot be greater than {max_name} ({max_val})",
            )

    # Step 1: Build and execute Stock-level query
    stock_query = select(Stock).where(Stock.is_active == True)

    if sector:
        stock_query = stock_query.where(Stock.sector == sector)
    if bist30:
        stock_query = stock_query.where(Stock.is_bist30 == True)
    if bist100:
        stock_query = stock_query.where(Stock.is_bist100 == True)
    if bist250:
        stock_query = stock_query.where(Stock.is_bist250 == True)
    if score_min is not None:
        stock_query = stock_query.where(Stock.overall_score >= score_min)
    if score_max is not None:
        stock_query = stock_query.where(Stock.overall_score <= score_max)
    if recommendation:
        stock_query = stock_query.where(Stock.recommendation == recommendation)
    if market_cap_min is not None:
        stock_query = stock_query.where(Stock.market_cap >= market_cap_min)
    if market_cap_max is not None:
        stock_query = stock_query.where(Stock.market_cap <= market_cap_max)
    if daily_change_min is not None:
        stock_query = stock_query.where(Stock.daily_change_pct >= daily_change_min)
    if daily_change_max is not None:
        stock_query = stock_query.where(Stock.daily_change_pct <= daily_change_max)

    stock_sort_columns = {
        "symbol": Stock.symbol,
        "current_price": Stock.current_price,
        "daily_change_pct": Stock.daily_change_pct,
        "market_cap": Stock.market_cap,
        "technical_score": Stock.technical_score,
        "fundamental_score": Stock.fundamental_score,
        "sentiment_score": Stock.sentiment_score,
        "overall_score": Stock.overall_score,
    }
    sort_col = stock_sort_columns.get(sort_by, Stock.overall_score)
    stock_query = stock_query.order_by(sort_col.desc().nullslast())

    stock_result = await db.execute(stock_query)
    stocks = stock_result.scalars().all()

    # Step 2: Batch-fetch latest fundamentals for matched stocks
    stock_ids = [s.id for s in stocks]
    fund_by_stock: Dict[int, Optional[Fundamental]] = {}

    if stock_ids:
        # DISTINCT ON stock_id ordered by updated_at desc — one row per stock
        fund_result = await db.execute(
            select(Fundamental)
            .where(Fundamental.stock_id.in_(stock_ids))
            .order_by(Fundamental.stock_id, Fundamental.updated_at.desc())
        )
        all_funds = fund_result.scalars().all()
        # Keep only the first (latest) record per stock_id
        for f in all_funds:
            if f.stock_id not in fund_by_stock:
                fund_by_stock[f.stock_id] = f

    # Step 3: Apply fundamental post-filters (only stocks with fundamental data pass)
    has_fund_filters = any([
        pe_ratio_min is not None,
        pe_ratio_max is not None,
        pb_ratio_min is not None,
        pb_ratio_max is not None,
        roe_min is not None,
        roe_max is not None,
        debt_to_equity_max is not None,
    ])

    def passes_fund_filters(s: Stock) -> bool:
        if not has_fund_filters:
            return True
        f = fund_by_stock.get(s.id)
        if f is None:
            return False
        if pe_ratio_min is not None and (f.pe_ratio is None or f.pe_ratio < pe_ratio_min):
            return False
        if pe_ratio_max is not None and (f.pe_ratio is None or f.pe_ratio > pe_ratio_max):
            return False
        if pb_ratio_min is not None and (f.pb_ratio is None or f.pb_ratio < pb_ratio_min):
            return False
        if pb_ratio_max is not None and (f.pb_ratio is None or f.pb_ratio > pb_ratio_max):
            return False
        if roe_min is not None and (f.roe is None or f.roe < roe_min):
            return False
        if roe_max is not None and (f.roe is None or f.roe > roe_max):
            return False
        if debt_to_equity_max is not None and (f.debt_to_equity is None or f.debt_to_equity > debt_to_equity_max):
            return False
        return True

    filtered_stocks = [s for s in stocks if passes_fund_filters(s)]
    total_count = len(filtered_stocks)
    paged_stocks = filtered_stocks[offset: offset + limit]

    # Step 4: Build response
    stocks_data = []
    for s in paged_stocks:
        f = fund_by_stock.get(s.id)
        stocks_data.append({
            "symbol": s.symbol,
            "name": s.name,
            "sector": s.sector,
            "current_price": s.current_price,
            "daily_change_pct": s.daily_change_pct,
            "market_cap": s.market_cap,
            "is_bist30": s.is_bist30,
            "is_bist100": s.is_bist100,
            "is_bist250": s.is_bist250,
            "overall_score": s.overall_score,
            "technical_score": s.technical_score,
            "fundamental_score": s.fundamental_score,
            "recommendation": s.recommendation,
            "pe_ratio": f.pe_ratio if f is not None else None,
            "pb_ratio": f.pb_ratio if f is not None else None,
            "roe": f.roe if f is not None else None,
            "debt_to_equity": f.debt_to_equity if f is not None else None,
        })

    return {
        "count": total_count,
        "limit": limit,
        "offset": offset,
        "stocks": stocks_data,
    }
