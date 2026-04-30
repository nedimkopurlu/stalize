"""
Data Collector Service — BIST100 veri toplama orchestrator

Veri kaynakları:
1. Yahoo Finance (yfinance) — Hisse fiyatları, emtia, endeksler, döviz
2. İş Yatırım — Temel analiz verileri (scraping)
3. KAP — Bildirimler
4. TCMB — Makro ekonomik veriler
"""
from __future__ import annotations

import asyncio
import os
import time
import diskcache
import yfinance as yf
import pandas as pd
import requests
from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import logging
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.stock import Stock
from app.models.price import PriceHistory, CommodityPrice
from app.services.fundamental import FundamentalAnalysisEngine
from app.services.sentiment import SentimentAnalysisEngine

logger = logging.getLogger(__name__)
BLOOMBERGHT_API_BASE = "https://bbapiv2.ciner.com.tr/api/v1"
ISTANBUL_TZ = ZoneInfo("Europe/Istanbul")

# ─── YFINANCE RESULT-LEVEL CACHE ─────────────────────────────────────────────

YFINANCE_CACHE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../cache/yfinance")
)
os.makedirs(YFINANCE_CACHE_DIR, exist_ok=True)
_yf_cache = diskcache.Cache(YFINANCE_CACHE_DIR, size_limit=1_000_000_000)  # 1 GB cap


@dataclass(frozen=True)
class LiveBistQuote:
    """Foreks-sourced live/delayed BIST quote carried by BloombergHT's JSON API."""

    symbol: str
    last_price: float
    previous_close: float | None
    daily_change_pct: float | None
    high: float | None
    low: float | None
    volume_lot: float | None
    turnover_try: float | None
    as_of: datetime
    source: str = "BloombergHT/Foreks"


def _parse_tr_number(value) -> float | None:
    if value is None:
        return None

    text = str(value).strip().replace("%", "").replace("₺", "").replace(" ", "")
    if not text or text == "-":
        return None

    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    elif text.count(".") > 1:
        text = text.replace(".", "")

    try:
        return float(text)
    except ValueError:
        return None


def _parse_bloomberght_timestamp(value: str | None) -> datetime:
    if value:
        try:
            parsed = datetime.strptime(value.strip(), "%d/%m/%Y %H:%M:%S")
            return parsed.replace(tzinfo=ISTANBUL_TZ).astimezone(timezone.utc)
        except ValueError:
            logger.warning("BloombergHT timestamp parse edilemedi: %s", value)
    return datetime.now(timezone.utc)


def _parse_bloomberght_quote_items(items: dict) -> LiveBistQuote | None:
    symbol = (items.get("ibsSymbol") or "").upper().strip()
    last_price = _parse_tr_number(items.get("lastPrice"))
    if not symbol or last_price is None:
        return None

    return LiveBistQuote(
        symbol=symbol,
        last_price=last_price,
        previous_close=_parse_tr_number(items.get("prevPrice")),
        daily_change_pct=_parse_tr_number(items.get("percentChange")),
        high=_parse_tr_number(items.get("priceHigh")),
        low=_parse_tr_number(items.get("priceLow")),
        volume_lot=_parse_tr_number(items.get("volumeLot")),
        turnover_try=_parse_tr_number(items.get("volume")),
        as_of=_parse_bloomberght_timestamp(items.get("lastUpdateTime")),
    )


def _detail_slug_from_bloomberght_url(url: str | None) -> str | None:
    if not url:
        return None
    return url.rstrip("/").split("/")[-1] or None


async def _fetch_json_from_bloomberght(path: str) -> dict:
    url = f"{BLOOMBERGHT_API_BASE}/{path.lstrip('/')}"

    def _fetch():
        response = requests.get(
            url,
            timeout=20,
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0",
            },
        )
        response.raise_for_status()
        return response.json()

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch)


async def _fetch_bloomberght_stock_slugs(symbols: list[str]) -> dict[str, str]:
    cache_key = "bloomberght:stock_slugs"
    cached = _yf_cache.get(cache_key)
    if cached is not None:
        return {symbol: cached[symbol] for symbol in symbols if symbol in cached}

    payload = await _fetch_json_from_bloomberght("ekonomi/borsa/bist/tum/hisseler")
    items = (((payload.get("body") or {}).get("allStocks") or {}).get("items") or [])
    slug_map: dict[str, str] = {}
    for item in items:
        symbol = (item.get("sec_code") or item.get("ibsSymbol") or "").upper().strip()
        slug = _detail_slug_from_bloomberght_url(item.get("url"))
        if symbol and slug:
            slug_map[symbol] = slug

    if slug_map:
        _yf_cache.set(cache_key, slug_map, expire=3600)
    return {symbol: slug_map[symbol] for symbol in symbols if symbol in slug_map}


async def get_bloomberght_live_quotes(symbols: list[str]) -> dict[str, LiveBistQuote]:
    """Fetch live/delayed BIST quotes from BloombergHT's Foreks-backed JSON API."""
    slug_map = await _fetch_bloomberght_stock_slugs(symbols)
    if not slug_map:
        return {}

    semaphore = asyncio.Semaphore(6)

    async def _fetch_one(symbol: str, slug: str) -> LiveBistQuote | None:
        async with semaphore:
            try:
                payload = await _fetch_json_from_bloomberght(f"ekonomi/borsa/hisse/detay/{slug}")
                items = ((payload.get("body") or {}).get("stockMarketDetail") or {}).get("items") or {}
                quote = _parse_bloomberght_quote_items(items)
                if quote and quote.symbol == symbol:
                    return quote
            except Exception as exc:
                logger.warning("BloombergHT canlı fiyat alınamadı [%s]: %s", symbol, exc)
            return None

    results = await asyncio.gather(
        *[_fetch_one(symbol, slug) for symbol, slug in slug_map.items()]
    )
    return {quote.symbol: quote for quote in results if quote is not None}


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
        for attempt in range(3):
            try:
                ticker = yf.Ticker(yahoo_symbol)
                result = ticker.history(period=period)
                if result is None or result.empty:
                    logger.debug(f"yfinance returned empty data for {yahoo_symbol} (no data available)")
                    return pd.DataFrame()
                return result
            except Exception as e:
                if "rate" in str(e).lower() or "429" in str(e):
                    time.sleep(10 * (attempt + 1))
                else:
                    logger.warning(f"yfinance network error for {yahoo_symbol}: {type(e).__name__}")
                    raise
        logger.warning(f"yfinance rate limit exhausted for {yahoo_symbol} after 3 attempts")
        return pd.DataFrame()

    loop = asyncio.get_event_loop()
    hist = await loop.run_in_executor(None, _fetch)
    if not hist.empty:
        _yf_cache.set(key, hist, expire=300)
    return hist


async def get_yahoo_chart_history(yahoo_symbol: str, period: str = "5d") -> pd.DataFrame:
    """Fetch Yahoo chart JSON directly as a fallback for BIST symbols yfinance misses."""
    key = f"chart_history:{yahoo_symbol}:{period}"
    cached = _yf_cache.get(key)
    if cached is not None:
        return cached

    def _fetch():
        try:
            response = requests.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}",
                params={"range": period, "interval": "1d", "includePrePost": "false"},
                timeout=20,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            response.raise_for_status()
            payload = response.json()
            result = ((payload.get("chart") or {}).get("result") or [None])[0] or {}
            timestamps = result.get("timestamp") or []
            quote = (((result.get("indicators") or {}).get("quote") or [{}])[0] or {})
            if not timestamps or not quote:
                return pd.DataFrame()

            rows = []
            for index, ts in enumerate(timestamps):
                def _quote_value(key: str):
                    values = quote.get(key) or []
                    return values[index] if index < len(values) else None

                close = _quote_value("close")
                if close is None:
                    continue
                rows.append(
                    {
                        "Date": datetime.fromtimestamp(ts, tz=timezone.utc),
                        "Open": _quote_value("open"),
                        "High": _quote_value("high"),
                        "Low": _quote_value("low"),
                        "Close": close,
                        "Volume": _quote_value("volume"),
                    }
                )

            if not rows:
                return pd.DataFrame()

            frame = pd.DataFrame(rows).set_index("Date")
            regular_market_time = (result.get("meta") or {}).get("regularMarketTime")
            if regular_market_time:
                frame.attrs["as_of"] = datetime.fromtimestamp(regular_market_time, tz=timezone.utc)
            return frame
        except Exception as exc:
            logger.warning("Yahoo chart fallback failed for %s: %s", yahoo_symbol, exc)
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
        self.universe = list(settings.BIST100_UNIVERSE)
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
                canonical_is_bist100 = bool(canonical.get("is_bist100", True))
                canonical_is_bist250 = bool(canonical.get("is_bist250", True))
                canonical_market_tier = str(canonical.get("market_tier", "yıldız"))

                # Check if already exists
                result = await db.execute(select(Stock).where(Stock.symbol == symbol))
                existing = result.scalar_one_or_none()

                if existing:
                    existing.yahoo_symbol = yahoo_symbol
                    existing.is_bist100 = canonical_is_bist100
                    existing.is_bist250 = canonical_is_bist250
                    existing.market_tier = canonical_market_tier
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
                            is_bist100=canonical_is_bist100,
                            is_bist250=canonical_is_bist250,
                            market_tier=canonical_market_tier,
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
                            is_bist100=canonical_is_bist100,
                            is_bist250=canonical_is_bist250,
                            market_tier=canonical_market_tier,
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

    async def collect_live_bist_quotes(self) -> int:
        """
        Refresh current BIST100 quotes from BloombergHT's Foreks-backed JSON API.

        Yahoo can lag or rate-limit BIST symbols. This lightweight pass keeps the
        decision screens current with real delayed/live market quotes.
        """
        logger.info("📡 BloombergHT/Foreks canlı BIST fiyatları toplanıyor...")
        quotes = await get_bloomberght_live_quotes(self.symbols)
        if not quotes:
            logger.warning("BloombergHT/Foreks canlı fiyat kaynağı boş döndü.")
            return 0

        missing = sorted(set(self.symbols) - set(quotes))
        if missing:
            logger.warning("BloombergHT/Foreks canlı fiyat eksik semboller: %s", ", ".join(missing))

        updated = 0
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Stock).where(Stock.symbol.in_(list(quotes.keys()))))
            stocks = result.scalars().all()

            for stock in stocks:
                quote = quotes.get(stock.symbol)
                if quote is None:
                    continue

                stock.current_price = quote.last_price
                stock.daily_change_pct = quote.daily_change_pct
                stock.volume = quote.volume_lot
                stock.last_data_update = quote.as_of

                trade_date = quote.as_of.astimezone(ISTANBUL_TZ).date()
                open_price = quote.previous_close or quote.last_price
                high_price = quote.high or max(open_price, quote.last_price)
                low_price = quote.low or min(open_price, quote.last_price)

                existing = await db.execute(
                    select(PriceHistory).where(
                        and_(
                            PriceHistory.stock_id == stock.id,
                            PriceHistory.date == trade_date,
                        )
                    )
                )
                price = existing.scalar_one_or_none()
                if price is None:
                    price = PriceHistory(
                        stock_id=stock.id,
                        date=trade_date,
                        open=open_price,
                        high=high_price,
                        low=low_price,
                        close=quote.last_price,
                        volume=quote.volume_lot,
                    )
                    db.add(price)
                else:
                    price.open = price.open or open_price
                    price.high = high_price
                    price.low = low_price
                    price.close = quote.last_price
                    price.volume = quote.volume_lot

                updated += 1

            fallback_updated = 0
            for symbol in missing:
                hist = await get_yahoo_chart_history(f"{symbol}.IS", period="5d")
                if hist.empty:
                    continue
                await self._persist_stock_history(db, symbol, hist)
                fallback_updated += 1

            await db.commit()

        total_updated = updated + fallback_updated
        logger.info(
            "✅ Canlı fiyat güncellemesi tamamlandı: %s BloombergHT/Foreks, %s Yahoo fallback",
            updated,
            fallback_updated,
        )
        return total_updated

    async def live_price_refresh_needed(self, max_age_minutes: int = 60) -> bool:
        """Return True when active stock quote timestamps are missing or too old."""
        async with AsyncSessionLocal() as db:
            active_count = await db.scalar(select(func.count()).select_from(Stock).where(Stock.is_active))
            price_count = await db.scalar(
                select(func.count())
                .select_from(Stock)
                .where(and_(Stock.is_active, Stock.current_price.is_not(None), Stock.last_data_update.is_not(None)))
            )
            latest_update = await db.scalar(select(func.max(Stock.last_data_update)).where(Stock.is_active))

        if not active_count or price_count < active_count:
            return True
        if latest_update is None:
            return True
        if latest_update.tzinfo is None:
            latest_update = latest_update.replace(tzinfo=timezone.utc)
        age_minutes = (datetime.now(timezone.utc) - latest_update).total_seconds() / 60
        return age_minutes > max_age_minutes

    async def _collect_stock_prices(self, db: AsyncSession, symbol: str, period: str):
        """Collect price data for a single stock."""
        yahoo_symbol = f"{symbol}.IS"
        try:
            hist = await get_yahoo_chart_history(yahoo_symbol, period=period)

            if hist.empty:
                logger.warning(f"{symbol}: Yahoo fiyat kaynağı veri döndürmedi")
                return

            count = await self._persist_stock_history(db, symbol, hist)

            if count > 0:
                logger.info(f"  📊 {symbol}: {count} yeni fiyat kaydı eklendi")

        except Exception as e:
            logger.error(f"  ❌ {symbol} fiyat verisi hatası: {e}")

    async def _persist_stock_history(self, db: AsyncSession, symbol: str, hist: pd.DataFrame) -> int:
        """Persist an OHLCV history frame and refresh the stock's current quote fields."""
        result = await db.execute(select(Stock).where(Stock.symbol == symbol))
        stock = result.scalar_one_or_none()
        if not stock or hist.empty:
            return 0

        def _row_float(row, key: str, fallback: float | None = None) -> float | None:
            value = row.get(key, fallback)
            if value is None or pd.isna(value):
                return fallback
            return float(value)

        last = hist.iloc[-1]
        last_close = _row_float(last, "Close")
        if last_close is None:
            return 0

        stock.current_price = last_close
        if len(hist) >= 2:
            prev_close = _row_float(hist.iloc[-2], "Close")
            if prev_close not in (None, 0):
                stock.daily_change_pct = ((last_close - prev_close) / prev_close) * 100
        stock.volume = _row_float(last, "Volume")
        stock.last_data_update = hist.attrs.get("as_of") or datetime.now(timezone.utc)

        latest_trade_date = hist.index[-1].date()
        count = 0
        for date, row in hist.iterrows():
            trade_date = date.date()
            close_price = _row_float(row, "Close")
            if close_price is None:
                continue

            open_price = _row_float(row, "Open", close_price) or close_price
            high_price = _row_float(row, "High", max(open_price, close_price)) or max(open_price, close_price)
            low_price = _row_float(row, "Low", min(open_price, close_price)) or min(open_price, close_price)
            volume = _row_float(row, "Volume", 0.0)

            existing = await db.execute(
                select(PriceHistory).where(
                    and_(
                        PriceHistory.stock_id == stock.id,
                        PriceHistory.date == trade_date,
                    )
                )
            )
            price = existing.scalar_one_or_none()
            if price is not None:
                if trade_date == latest_trade_date:
                    price.open = open_price
                    price.high = high_price
                    price.low = low_price
                    price.close = close_price
                    price.volume = volume
                continue

            db.add(
                PriceHistory(
                    stock_id=stock.id,
                    date=trade_date,
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    close=close_price,
                    volume=volume,
                )
            )
            count += 1

        return count

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
                    hist = await get_yahoo_chart_history(sym, period=period)

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
        """Refresh intraday decision data without hammering slow yfinance fundamentals/news."""
        logger.info("🔄 Günlük veri güncelleme başlıyor...")
        await self.collect_price_data(period="5d")
        await self.collect_live_bist_quotes()
        await self.collect_market_data(period="5d")
        from app.services.technical import technical_engine
        from app.services.scoring import scoring_engine

        await technical_engine.analyze_all()
        await scoring_engine.update_all_scores()
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
