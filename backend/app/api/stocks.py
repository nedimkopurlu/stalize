"""Stock domain router — frontend'in kullandığı hisse verisi endpoint'leri."""
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


@router.post("/stocks/{symbol}/analyze")
async def analyze_stock(
    symbol: str,
    db: AsyncSession = Depends(get_db),
):
    """On-demand Gemini Türkçe hisse analizi üretir. Önbellek frontend sorumluluğundadır."""
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

    pe = f"{fund.pe_ratio:.1f}" if fund and fund.pe_ratio is not None else None
    pb = f"{fund.pb_ratio:.2f}" if fund and fund.pb_ratio is not None else None
    roe = f"{fund.roe * 100:.1f}%" if fund and fund.roe is not None else None
    market_cap = fund.market_cap if fund and fund.market_cap is not None else None
    dividend_yield = f"{fund.dividend_yield * 100:.2f}%" if fund and fund.dividend_yield is not None else None
    debt_equity = f"{fund.debt_to_equity:.2f}" if fund and fund.debt_to_equity is not None else None

    # Fiyat ve teknik bilgiler
    price = f"{stock.current_price:.2f} TL" if stock.current_price else "bilinmiyor"
    change = (f"%+.2f" % stock.daily_change_pct) if stock.daily_change_pct is not None else "bilinmiyor"
    score = f"{stock.overall_score:.1f}/100" if stock.overall_score else "bilinmiyor"
    rec = stock.recommendation or "bilinmiyor"
    sector = stock.sector or "bilinmiyor"
    name = stock.name or stock.symbol

    # Temel analiz satırları — sadece mevcut veriler
    fund_lines = []
    if pe:      fund_lines.append(f"  - F/K oranı: {pe} (sektör ortalamasıyla kıyasla)")
    if pb:      fund_lines.append(f"  - PD/DD oranı: {pb}")
    if roe:     fund_lines.append(f"  - Öz sermaye getirisi (ROE): {roe}")
    if dividend_yield: fund_lines.append(f"  - Temettü verimi: {dividend_yield}")
    if debt_equity:    fund_lines.append(f"  - Borç/Öz Sermaye: {debt_equity}")
    if market_cap:
        mc_b = market_cap / 1e9
        fund_lines.append(f"  - Piyasa değeri: {mc_b:.1f} Milyar TL")

    fund_section = "\n".join(fund_lines) if fund_lines else "  - Temel veriler mevcut değil"

    prompt = f"""Aşağıdaki verilere dayanarak {name} ({stock.symbol}) hissesi için kapsamlı bir yatırım analizi yaz.

## Hisse Verileri
- Sektör: {sector}
- Güncel Fiyat: {price}
- Günlük Değişim: {change}
- Model Skoru: {score}
- Sistem Önerisi: {rec}

## Temel Analiz Verileri
{fund_section}

## Analiz Talimatları
1. Bu verileri bir araya getirerek {stock.symbol} hakkında bütünsel bir değerlendirme yap
2. Değerleme çarpanlarını (F/K, PD/DD) yorumla — ucuz mu pahalı mı?
3. ROE ve karlılık göstergelerini değerlendir
4. Model skorunu ve öneriyi temel verilerle ilişkilendir
5. Mevcut piyasa koşullarında (Türkiye ekonomisi, enflasyon, faiz) bu sektörün durumunu kısaca belirt
6. Net bir sonuç: Bu hissede fırsat var mı, risk nedir?

Analizi Türkçe, akıcı paragraflar halinde yaz. Madde listesi kullanma."""

    analysis_text = await gemini_service.generate(prompt)

    return {
        "symbol": stock.symbol,
        "analysis": analysis_text,
        "cached": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
