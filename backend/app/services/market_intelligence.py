"""
Market event service

KAP ve makro haber akışını tek merkezde birleştirir, önceliklendirir ve deduplicate eder.
"""
import asyncio
import html
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.news import NewsItem
from app.models.stock import Stock
from app.services.external_news_rss import external_news_rss_collector
from app.services.kap_parser import kap_parser

logger = logging.getLogger(__name__)


class MarketIntelligenceService:
    """KAP + makro + senaryo birleştirme servisi."""

    OVERVIEW_CACHE_TTL_SECONDS = 10

    FEED_MAX_AGE_HOURS = {
        "KAP": 72,
        "TCMB": 720,
        "TUIK": 1080,
        "HMB": 168,
        "Borsa İstanbul": 168,
        "MKK": 168,
        "Takasbank": 168,
        "Bloomberg HT": 72,
        "Ekonomim": 72,
        "Dünya": 72,
        "CNBC-e": 72,
        "Bigpara": 72,
        "A Para": 72,
        "Borsa Gündem": 72,
        "Finans Gündem": 72,
        "Para Analiz": 72,
        "Mynet Finans": 72,
        "Foreks": 72,
        "Borsa Direkt": 72,
        "InvestAZ": 72,
    }

    OFFICIAL_INTELLIGENCE_SOURCES = {
        "TCMB",
        "TUIK",
        "HMB",
        "Borsa İstanbul",
        "MKK",
        "Takasbank",
    }

    TURKEY_NEWS_SOURCES = OFFICIAL_INTELLIGENCE_SOURCES | {
        "KAP",
        "Bloomberg HT",
        "Ekonomim",
        "Dünya",
        "Dunya",
        "CNBC-e",
        "Bigpara",
        "A Para",
        "Borsa Gündem",
        "Finans Gündem",
        "Para Analiz",
        "Mynet Finans",
        "Foreks",
        "Borsa Direkt",
        "InvestAZ",
    }

    TURKEY_SOURCE_DOMAINS = (
        "kap.org.tr",
        "tcmb.gov.tr",
        "tuik.gov.tr",
        "hmb.gov.tr",
        "borsaistanbul.com",
        "mkk.com.tr",
        "takasbank.com.tr",
        "bloomberght.com",
        "ekonomim.com",
        "dunya.com",
        "cnbce.com",
        "bigpara.hurriyet.com.tr",
        "apara.com.tr",
        "borsagundem.com.tr",
        "finansgundemi.com",
        "paraanaliz.com",
        "finans.mynet.com",
        "foreks.com",
        "borsadirekt.com",
        "investaz.com.tr",
        "news.google.com",
    )

    def __init__(self) -> None:
        self._overview_cache: Dict[int, Tuple[datetime, Dict]] = {}

    def _normalize_text(self, value: str) -> str:
        mapping = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
        return value.translate(mapping).lower()

    def _source_rank(self, source: str) -> int:
        normalized_source = self._normalize_text(source or "")
        try:
            return next(
                index
                for index, candidate in enumerate(settings.SOURCE_PRIORITY)
                if self._normalize_text(candidate) == normalized_source
            )
        except StopIteration:
            return len(settings.SOURCE_PRIORITY) + 1

    def _parse_timestamp(self, value: str) -> datetime:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return datetime.min.replace(tzinfo=timezone.utc)

    def _max_age_hours(self, item: Dict) -> int:
        source = item.get("publisher") or item.get("source") or ""
        category = item.get("category") or ""
        if category == "company":
            return 72
        if category == "macro":
            return self.FEED_MAX_AGE_HOURS.get(source, 720)
        return self.FEED_MAX_AGE_HOURS.get(source, 72)

    def _is_fresh_enough(self, item: Dict) -> bool:
        timestamp = self._parse_timestamp(item.get("timestamp", ""))
        if timestamp == datetime.min.replace(tzinfo=timezone.utc):
            return False
        age = datetime.now(timezone.utc) - timestamp.astimezone(timezone.utc)
        return age <= timedelta(hours=self._max_age_hours(item))

    def _is_turkey_scope_item(self, item: Dict) -> bool:
        source = item.get("publisher") or item.get("source") or ""
        source_ok = source in self.TURKEY_NEWS_SOURCES
        url = (item.get("source_url") or item.get("url") or "").lower()
        domain_ok = any(domain in url for domain in self.TURKEY_SOURCE_DOMAINS)
        return source_ok and (domain_ok or not url)

    def _recency_score(self, item: Dict) -> float:
        timestamp = self._parse_timestamp(item.get("timestamp", ""))
        if timestamp == datetime.min.replace(tzinfo=timezone.utc):
            return float("inf")
        return max(0.0, (datetime.now(timezone.utc) - timestamp.astimezone(timezone.utc)).total_seconds() / 3600)

    def _dedupe_key(self, item: Dict) -> Tuple[str, str]:
        headline = self._normalize_text(
            (item.get("headline") or item.get("summary", {}).get("headline") or "").strip()
        )
        url = (item.get("source_url") or item.get("url") or item.get("scenario", {}).get("source_url") or "").strip().lower()
        return headline, url

    def _event_priority(self, item: Dict) -> Tuple[int, float, float]:
        source = item.get("publisher") or item.get("source") or "Unknown"
        source_rank = self._source_rank(source)
        importance = float(item.get("importance_score", 0.0) or 0.0)
        sentiment = abs(float(item.get("sentiment_score", 0.0) or 0.0))
        horizon_rank = 0 if item.get("thesis_horizon") == "medium_term" else 1
        return horizon_rank, source_rank, -importance, -sentiment

    def _direction_from_scores(self, sentiment_score: Optional[float]) -> str:
        score = float(sentiment_score or 0.0)
        return "up" if score >= 0 else "down"

    def _magnitude_from_importance(self, importance_score: Optional[float]) -> str:
        importance = float(importance_score or 0.0)
        if importance >= 0.93:
            return "extreme"
        if importance >= 0.85:
            return "high"
        if importance >= 0.7:
            return "medium"
        return "low"

    def _is_market_relevant_official_item(self, source: Optional[str], headline: str) -> bool:
        if source != "HMB":
            return True

        normalized = self._normalize_text(headline)
        blocked_keywords = (
            "uzman yardimciligi",
            "giris sinavi",
            "personel",
            "kariyer",
            "basvuru",
            "staj",
        )
        return not any(keyword in normalized for keyword in blocked_keywords)

    async def get_official_feed(self, limit: int = 20) -> List[Dict]:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(NewsItem, Stock.symbol)
                .join(Stock, NewsItem.stock_id == Stock.id, isouter=True)
                .where(NewsItem.source.in_(self.OFFICIAL_INTELLIGENCE_SOURCES))
                .order_by(NewsItem.published_at.desc(), NewsItem.id.desc())
                .limit(max(limit * 3, 30))
            )
            rows = result.all()

        feed: List[Dict] = []
        for news, symbol in rows:
            headline = html.unescape(news.title or "")
            if not self._is_market_relevant_official_item(news.source, headline):
                continue
            feed.append(
                {
                    "trigger_id": (symbol.lower() if symbol else (news.source or "official").lower().replace(" ", "_")),
                    "direction": self._direction_from_scores(news.sentiment_score),
                    "magnitude": self._magnitude_from_importance(news.importance_score),
                    "headline": headline,
                    "original_headline": headline,
                    "source_url": news.url,
                    "publisher": news.source,
                    "sentiment_score": news.sentiment_score or 0.0,
                    "timestamp": news.published_at.isoformat() if news.published_at else "",
                    "category": news.category,
                    "importance_score": news.importance_score,
                    "symbol": symbol,
                    "thesis_horizon": "medium_term" if (news.importance_score or 0) >= 0.8 else "short_term",
                }
            )

        return feed[:limit]

    async def get_unified_feed(self, limit: int = 20) -> List[Dict]:
        kap_feed, official_feed, external_rss_feed = await asyncio.gather(
            kap_parser.get_recent_feed(limit=limit),
            self.get_official_feed(limit=limit),
            external_news_rss_collector.fetch_market_news(limit=limit),
        )
        merged = [
            item
            for item in [*kap_feed, *official_feed, *external_rss_feed]
            if self._is_fresh_enough(item) and self._is_turkey_scope_item(item)
        ]

        deduped: Dict[Tuple[str, str], Dict] = {}
        for item in merged:
            key = self._dedupe_key(item)
            current = deduped.get(key)
            if current is None or self._event_priority(item) < self._event_priority(current):
                deduped[key] = item

        ranked = sorted(
            deduped.values(),
            key=lambda item: (
                self._event_priority(item),
                self._recency_score(item),
            ),
        )
        return ranked[:limit]

    async def get_unified_scenarios(self, limit: int = 10) -> List[Dict]:
        scenarios = await kap_parser.get_recent_scenarios(limit=limit * 3)

        deduped: Dict[Tuple[str, str], Dict] = {}
        for scenario in scenarios:
            computed_at = scenario.get("computed_at") or scenario.get("scenario", {}).get("computed_at") or ""
            scenario_item = {
                "timestamp": computed_at,
                "publisher": scenario.get("scenario", {}).get("publisher"),
                "category": "company",
            }
            if not self._is_fresh_enough(scenario_item):
                continue
            key = self._dedupe_key({
                "headline": scenario["summary"]["headline"],
                "source_url": scenario["scenario"].get("source_url", ""),
            })
            current = deduped.get(key)
            current_score = max((abs(item["impact_score"]) for item in current["impacts"]), default=0) if current else -1
            next_score = max((abs(item["impact_score"]) for item in scenario["impacts"]), default=0)
            if current is None or next_score > current_score:
                deduped[key] = scenario

        ranked = sorted(
            deduped.values(),
            key=lambda scenario: (
                -scenario["summary"]["total_stocks_affected"],
                -max((abs(item["impact_score"]) for item in scenario["impacts"]), default=0),
                self._source_rank(scenario["scenario"].get("publisher") or "Unknown"),
            ),
        )
        return ranked[:limit]

    async def get_overview(self, limit: int = 10) -> Dict:
        cache_key = max(1, int(limit))
        cached = self._overview_cache.get(cache_key)
        if cached:
            cached_at, payload = cached
            age = (datetime.now(timezone.utc) - cached_at).total_seconds()
            if age < self.OVERVIEW_CACHE_TTL_SECONDS:
                return {
                    **payload,
                    "cache": {
                        "status": "hit",
                        "age_seconds": round(age, 2),
                        "ttl_seconds": self.OVERVIEW_CACHE_TTL_SECONDS,
                    },
                }

        feed, scenarios = await asyncio.gather(
            self.get_unified_feed(limit=limit),
            self.get_unified_scenarios(limit=limit),
        )

        source_summary: Dict[str, int] = {}
        horizon_summary: Dict[str, int] = {}
        for item in feed:
            source = item.get("publisher") or item.get("source") or "Unknown"
            source_summary[source] = source_summary.get(source, 0) + 1
            horizon = item.get("thesis_horizon") or "short_term"
            horizon_summary[horizon] = horizon_summary.get(horizon, 0) + 1

        payload = {
            "feed": feed,
            "scenarios": scenarios,
            "source_summary": source_summary,
            "horizon_summary": horizon_summary,
            "priority_mode": settings.NEWS_PRIORITIZATION_MODE,
            "primary_source": settings.PRIMARY_DISCLOSURE_SOURCE,
            "scope": {
                "language": "tr",
                "region": "TR",
                "source_policy": "turkiye_only",
            },
            "cache": {
                "status": "miss",
                "age_seconds": 0,
                "ttl_seconds": self.OVERVIEW_CACHE_TTL_SECONDS,
            },
        }
        self._overview_cache[cache_key] = (datetime.now(timezone.utc), payload)
        return payload


market_intelligence_service = MarketIntelligenceService()
