"""
Data Collector Service — BIST100 veri toplama orchestrator

Veri kaynakları:
1. Yahoo Finance (yfinance) — Hisse fiyatları, emtia, endeksler, döviz
2. İş Yatırım — Temel analiz verileri (scraping)
3. KAP — Bildirimler
4. TCMB — Makro ekonomik veriler
"""
import asyncio
import os
import diskcache
import yfinance as yf
import pandas as pd
from datetime import datetime
import logging
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.stock import Stock
from app.models.price import PriceHistory, CommodityPrice
from app.services.fundamental import FundamentalAnalysisEngine
from app.services.sentiment import SentimentAnalysisEngine

logger = logging.getLogger(__name__)

# ─── YFINANCE RESULT-LEVEL CACHE ─────────────────────────────────────────────

YFINANCE_CACHE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../cache/yfinance")
)
os.makedirs(YFINANCE_CACHE_DIR, exist_ok=True)
_yf_cache = diskcache.Cache(YFINANCE_CACHE_DIR)


async def get_ticker_history(yahoo_symbol: str, period: str = "5d") -> pd.DataFrame:
    """
    Fetch ticker.history(period) with result-level diskcache.
    Price data TTL: 300 seconds (5 minutes).
    Empty DataFrames are NOT cached (guard against Yahoo error responses).
    Cache check is synchronous (fast local disk); only the Yahoo HTTP call is offloaded.
    """
    key = f"history:{yahoo_symbol}:{period}"
    cached = _yf_cache.get(key)
    if cached is not None:
        logger.debug(f"yfinance cache hit: {key}")
        return cached

    def _fetch():
        import time
        for attempt in range(3):
            try:
                ticker = yf.Ticker(yahoo_symbol)
                return ticker.history(period=period)
            except Exception as e:
                if "rate" in str(e).lower() or "429" in str(e):
                    time.sleep(10 * (attempt + 1))
                else:
                    raise
        return pd.DataFrame()

    loop = asyncio.get_event_loop()
    hist = await loop.run_in_executor(None, _fetch)
    if not hist.empty:
        _yf_cache.set(key, hist, expire=300)
    return hist


async def get_ticker_info(yahoo_symbol: str) -> dict:
    """
    Fetch ticker.info with result-level diskcache.
    Fundamental data TTL: 86400 seconds (24 hours).
    Empty dicts are NOT cached.
    Cache check is synchronous (fast local disk); only the Yahoo HTTP call is offloaded.
    """
    key = f"info:{yahoo_symbol}"
    cached = _yf_cache.get(key)
    if cached is not None:
        logger.debug(f"yfinance info cache hit: {key}")
        return cached

    def _fetch():
        ticker = yf.Ticker(yahoo_symbol)
        return ticker.info or {}

    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, _fetch)
    if info:
        _yf_cache.set(key, info, expire=86400)
    return info


class DataCollector:
    """Main data collection orchestrator for Borsa İstanbul stocks."""

    def __init__(self):
        self.universe = list(settings.BIST_FULL_UNIVERSE)
        self.symbols = [item["symbol"] for item in self.universe]
        self._universe_by_symbol = {item["symbol"]: item for item in self.universe}
        self.commodity_symbols = settings.COMMODITY_SYMBOLS
        self.index_symbols = settings.INDEX_SYMBOLS
        self.currency_pairs = settings.CURRENCY_PAIRS
        self.bond_symbols = settings.BOND_SYMBOLS

    # ─── STOCK INITIALIZATION ────────────────────────────────────────────

    async def initialize_stocks(self):
        """Initialize BIST100 stocks in database with metadata from Yahoo Finance."""
        logger.info(f"📊 BIST100 hisseleri veritabanına ekleniyor ({len(self.symbols)} hisse)...")

        async with AsyncSessionLocal() as db:
            processed = 0
            for symbol in self.symbols:
                yahoo_symbol = f"{symbol}.IS"
                canonical = self._universe_by_symbol[symbol]
                canonical_name = str(canonical["name"])
                canonical_sector = str(canonical["sector"])
                canonical_is_bist30 = bool(canonical["is_bist30"])

                # Check if already exists
                result = await db.execute(select(Stock).where(Stock.symbol == symbol))
                existing = result.scalar_one_or_none()

                if existing:
                    existing.yahoo_symbol = yahoo_symbol
                    existing.is_bist100 = bool(canonical.get("is_bist100", False))
                    existing.is_bist250 = bool(canonical.get("is_bist250", False))
                    existing.market_tier = str(canonical.get("market_tier", "ana"))
                    existing.is_active = True
                    existing.name = canonical_name
                    existing.sector = canonical_sector
                    existing.is_bist30 = canonical_is_bist30
                else:
                    # Fetch info from Yahoo Finance
                    try:
                        info = await get_ticker_info(yahoo_symbol)

                        stock = Stock(
                            symbol=symbol,
                            yahoo_symbol=yahoo_symbol,
                            name=canonical_name,
                            sector=canonical_sector,
                            industry=info.get("industry"),
                            market_cap=info.get("marketCap"),
                            current_price=info.get("currentPrice") or info.get("regularMarketPrice"),
                            daily_change_pct=info.get("regularMarketChangePercent"),
                            volume=info.get("regularMarketVolume"),
                            is_bist30=canonical_is_bist30,
                            is_bist100=bool(canonical.get("is_bist100", False)),
                            is_bist250=bool(canonical.get("is_bist250", False)),
                            market_tier=str(canonical.get("market_tier", "ana")),
                            is_active=True,
                        )
                        db.add(stock)
                        logger.info(f"  ✅ {symbol} — {stock.name}")
                    except Exception as e:
                        logger.warning(f"  ⚠️ {symbol} bilgisi alınamadı: {e}")
                        # Add with minimal info
                        stock = Stock(
                            symbol=symbol,
                            yahoo_symbol=yahoo_symbol,
                            name=canonical_name,
                            sector=canonical_sector,
                            is_bist30=canonical_is_bist30,
                            is_bist100=bool(canonical.get("is_bist100", False)),
                            is_bist250=bool(canonical.get("is_bist250", False)),
                            market_tier=str(canonical.get("market_tier", "ana")),
                            is_active=True,
                        )
                        db.add(stock)

                processed += 1
                if processed % 10 == 0:
                    await db.commit()
                    await asyncio.sleep(1)
                    logger.info(f"  ⏱️ {processed}/{len(self.symbols)} hisse işlendi")

            await self._deactivate_noncanonical_stocks(db)
            await db.commit()
            logger.info("✅ BIST100 hisseleri veritabanına eklendi")

    # ─── PRICE DATA COLLECTION ───────────────────────────────────────────

    async def collect_price_data(self, period: str = "5y"):
        """Collect OHLCV price data for all BIST100 stocks."""
        logger.info(f"📈 Fiyat verileri toplanıyor (period={period})...")

        async with AsyncSessionLocal() as db:
            for i, symbol in enumerate(self.symbols):
                try:
                    await self._collect_stock_prices(db, symbol, period)
                except Exception as e:
                    logger.warning(f"  ⚠️ {symbol} fiyat verisi atlandı: {e}")
                if (i + 1) % 10 == 0:
                    await db.commit()
                    await asyncio.sleep(1)
            await db.commit()

        logger.info("✅ Fiyat verileri toplandı")

    async def _collect_stock_prices(self, db: AsyncSession, symbol: str, period: str):
        """Collect price data for a single stock."""
        yahoo_symbol = f"{symbol}.IS"
        try:
            hist = await get_ticker_history(yahoo_symbol, period=period)

            if hist.empty:
                logger.warning(f"  ⚠️ {symbol}: Veri yok")
                return

            # Get stock ID
            result = await db.execute(select(Stock).where(Stock.symbol == symbol))
            stock = result.scalar_one_or_none()
            if not stock:
                return

            # Update current price
            if not hist.empty:
                last = hist.iloc[-1]
                stock.current_price = float(last["Close"])
                if len(hist) >= 2:
                    prev = hist.iloc[-2]["Close"]
                    stock.daily_change_pct = ((last["Close"] - prev) / prev) * 100
                stock.volume = float(last["Volume"]) if "Volume" in last else None
                stock.last_data_update = datetime.now()

            count = 0
            for date, row in hist.iterrows():
                trade_date = date.date()

                # Check if exists
                existing = await db.execute(
                    select(PriceHistory).where(
                        and_(
                            PriceHistory.stock_id == stock.id,
                            PriceHistory.date == trade_date,
                        )
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                price = PriceHistory(
                    stock_id=stock.id,
                    date=trade_date,
                    open=float(row.get("Open", 0)),
                    high=float(row.get("High", 0)),
                    low=float(row.get("Low", 0)),
                    close=float(row["Close"]),
                    volume=float(row.get("Volume", 0)),
                )
                db.add(price)
                count += 1

            if count > 0:
                logger.info(f"  📊 {symbol}: {count} yeni fiyat kaydı eklendi")

        except Exception as e:
            logger.error(f"  ❌ {symbol} fiyat verisi hatası: {e}")

    # ─── COMMODITY / INDEX / CURRENCY DATA ───────────────────────────────

    async def collect_market_data(self, period: str = "2y"):
        """Collect commodity, index, currency, and bond data."""
        logger.info("🌍 Piyasa verileri toplanıyor...")

        all_symbols = {}

        # Commodities
        for name, sym in self.commodity_symbols.items():
            all_symbols[sym] = {"name": name, "category": "commodity"}

        # Indices
        for name, sym in self.index_symbols.items():
            all_symbols[sym] = {"name": name, "category": "index"}

        # Currencies
        for name, sym in self.currency_pairs.items():
            all_symbols[sym] = {"name": name, "category": "currency"}

        # Bonds
        for name, sym in self.bond_symbols.items():
            all_symbols[sym] = {"name": name, "category": "bond"}

        async with AsyncSessionLocal() as db:
            for sym, meta in all_symbols.items():
                try:
                    hist = await get_ticker_history(sym, period=period)

                    if hist.empty:
                        logger.warning(f"  ⚠️ {sym} ({meta['name']}): Veri yok")
                        continue

                    count = 0
                    for date, row in hist.iterrows():
                        trade_date = date.date()

                        existing = await db.execute(
                            select(CommodityPrice).where(
                                and_(
                                    CommodityPrice.symbol == sym,
                                    CommodityPrice.date == trade_date,
                                )
                            )
                        )
                        if existing.scalar_one_or_none():
                            continue

                        cp = CommodityPrice(
                            symbol=sym,
                            name=meta["name"],
                            category=meta["category"],
                            date=trade_date,
                            open=float(row.get("Open", 0)),
                            high=float(row.get("High", 0)),
                            low=float(row.get("Low", 0)),
                            close=float(row["Close"]),
                            volume=float(row.get("Volume", 0)) if "Volume" in row else None,
                        )
                        db.add(cp)
                        count += 1

                    if count > 0:
                        logger.info(f"  🌍 {meta['name']} ({sym}): {count} kayıt eklendi")

                except Exception as e:
                    logger.error(f"  ❌ {sym} ({meta['name']}) hatası: {e}")

            await db.commit()
        logger.info("✅ Piyasa verileri toplandı")

    # ─── FUNDAMENTAL DATA COLLECTION ─────────────────────────────────────

    async def collect_fundamentals(self):
        """Collect fundamental data for all BIST100 stocks."""
        logger.info("📑 Temel analiz verileri toplanıyor...")
        
        engine = FundamentalAnalysisEngine()
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Stock))
            stocks = result.scalars().all()
            
            for stock in stocks:
                if stock.is_active:
                    await engine.analyze_stock(db, stock)
                    
        logger.info("✅ Temel analiz verileri toplandı")

    # ─── NEWS & SENTIMENT DATA COLLECTION ─────────────────────────────────

    async def collect_sentiment(self):
        """Analyze news sentiment for all BIST100 stocks."""
        logger.info("📰 Haber duygu analizi toplanıyor...")
        
        # 1. İlk olarak KAP bildirimlerini çek (En yüksek öncelik)
        from app.services.kap_parser import run_kap_scan
        await run_kap_scan()
        
        # 2. Genel haber ve yfinance analizi
        engine = SentimentAnalysisEngine()
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Stock))
            stocks = result.scalars().all()
            
            for stock in stocks:
                if stock.is_active:
                    await engine.analyze_stock(db, stock)
                    
        logger.info("✅ Duygu analizleri tamamlandı")

    # ─── DAILY UPDATE ────────────────────────────────────────────────────

    async def daily_update(self):
        """Run daily data collection for all sources."""
        logger.info("🔄 Günlük veri güncelleme başlıyor...")
        await self.collect_price_data(period="5d")
        await self.collect_market_data(period="5d")
        await self.collect_fundamentals()
        await self.collect_sentiment()
        logger.info("✅ Günlük güncelleme tamamlandı")

    # ─── FULL INITIAL LOAD ───────────────────────────────────────────────

    async def full_initial_load(self):
        """Complete initial data load — run once on first setup."""
        logger.info("🚀 İlk veri yüklemesi başlıyor...")
        await self.initialize_stocks()
        await self.collect_price_data(period="5y")
        await self.collect_market_data(period="2y")
        await self.collect_fundamentals()
        await self.collect_sentiment()
        logger.info("🎉 İlk veri yüklemesi tamamlandı!")

    # ─── HELPERS ─────────────────────────────────────────────────────────

    async def _deactivate_noncanonical_stocks(self, db: AsyncSession) -> None:
        """Kanonik evren dışında kalan eski hisseleri pasife al."""
        result = await db.execute(select(Stock).where(Stock.symbol.not_in(self.symbols)))
        legacy_stocks = result.scalars().all()
        for stock in legacy_stocks:
            if stock.is_active or stock.is_bist100:
                stock.is_active = False
                stock.is_bist100 = False
                stock.is_bist30 = False
                logger.info(f"  🧹 Pasife alındı: {stock.symbol} — kanonik evren dışında")


# Singleton instance
data_collector = DataCollector()
