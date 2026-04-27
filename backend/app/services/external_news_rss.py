from __future__ import annotations

import asyncio
import html
import logging
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional, Tuple

import feedparser

from app.services.macro_news import macro_news_collector
from app.services.translator import financial_translator


logger = logging.getLogger(__name__)


class ExternalNewsRSSCollector:
    """Public RSS-based global market news collector."""

    MAX_AGE_HOURS = 72

    FEEDS: list[dict[str, Any]] = [
        {
            "key": "reuters_markets",
            "publisher": "Reuters",
            "url": "https://news.google.com/rss/search?q=site:reuters.com+markets&hl=en-US&gl=US&ceid=US:en",
            "trigger_id": "bist100_index",
            "base_importance": 0.82,
        },
        {
            "key": "cnbc_markets",
            "publisher": "CNBC",
            "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
            "trigger_id": "bist100_index",
            "base_importance": 0.76,
        },
        {
            "key": "ft_markets",
            "publisher": "Financial Times",
            "url": "https://news.google.com/rss/search?q=site:ft.com+markets&hl=en-US&gl=US&ceid=US:en",
            "trigger_id": "bist100_index",
            "base_importance": 0.8,
        },
        {
            "key": "yahoo_finance",
            "publisher": "Yahoo Finance",
            "url": "https://finance.yahoo.com/news/rssindex",
            "trigger_id": "bist100_index",
            "base_importance": 0.7,
        },
        {
            "key": "marketwatch_marketpulse",
            "publisher": "MarketWatch",
            "url": "https://feeds.content.dowjones.io/public/rss/mw_marketpulse",
            "trigger_id": "bist100_index",
            "base_importance": 0.68,
        },
        {
            "key": "investing_stock",
            "publisher": "Investing",
            "url": "https://www.investing.com/rss/news_25.rss",
            "trigger_id": "bist100_index",
            "base_importance": 0.64,
        },
        {
            "key": "investing_forex",
            "publisher": "Investing",
            "url": "https://www.investing.com/rss/news_1.rss",
            "trigger_id": "usd_try",
            "base_importance": 0.72,
        },
        {
            "key": "investing_economic",
            "publisher": "Investing",
            "url": "https://www.investing.com/rss/news_95.rss",
            "trigger_id": "macro_calendar",
            "base_importance": 0.78,
        },
        {
            "key": "bloomberght",
            "publisher": "Bloomberg HT",
            "url": "https://news.google.com/rss/search?q=site:bloomberght.com+borsa&hl=tr&gl=TR&ceid=TR:tr",
            "trigger_id": "bist100_index",
            "base_importance": 0.74,
        },
        {
            "key": "ekonomim",
            "publisher": "Ekonomim",
            "url": "https://news.google.com/rss/search?q=site:ekonomim.com+borsa&hl=tr&gl=TR&ceid=TR:tr",
            "trigger_id": "bist100_index",
            "base_importance": 0.68,
        },
        {
            "key": "dunya",
            "publisher": "Dunya",
            "url": "https://news.google.com/rss/search?q=site:dunya.com+borsa&hl=tr&gl=TR&ceid=TR:tr",
            "trigger_id": "bist100_index",
            "base_importance": 0.66,
        },
    ]

    BLOCKED_PATTERNS = (
        "should i ",
        "retire at",
        "my adviser",
        "complain",
        "nonprofit job",
        "commute",
        "form 4",
        "form 13g",
        "director sells",
        "insider trading",
        "company stock",
        "common stock",
        "personal finance",
    )

    RELEVANCE_PATTERNS = (
        "market",
        "stocks",
        "shares",
        "bond",
        "yield",
        "forex",
        "dollar",
        "euro",
        "lira",
        "oil",
        "gold",
        "inflation",
        "interest rate",
        "fed",
        "central bank",
        "economy",
        "tariff",
        "trade",
        "iran",
        "china",
        "europe",
        "u.s.",
        "bank",
        "growth",
        "recession",
        "jobless",
        "consumer sentiment",
        "payrolls",
        "treasury",
        "commodity",
        "crypto",
    )

    def _normalize_text(self, value: str) -> str:
        mapping = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
        return value.translate(mapping).lower()

    def _parse_timestamp_dt(self, value: Optional[str]) -> datetime:
        if not value:
            return datetime.now(timezone.utc)

        candidates = [value]
        if "T" not in value and re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", value):
            candidates.insert(0, value.replace(" ", "T") + "+00:00")

        for candidate in candidates:
            try:
                if "," in candidate:
                    parsed = parsedate_to_datetime(candidate)
                else:
                    parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)
            except Exception:
                continue

        return datetime.now(timezone.utc)

    def _is_relevant(self, title: str, summary: str, feed_key: str) -> bool:
        normalized = self._normalize_text(f"{title} {summary}")
        if any(pattern in normalized for pattern in self.BLOCKED_PATTERNS):
            return False

        if feed_key.startswith("investing_"):
            return True

        return any(pattern in normalized for pattern in self.RELEVANCE_PATTERNS)

    def _normalize_entry(self, entry: Any, feed_def: dict[str, Any]) -> Optional[dict[str, Any]]:
        title = html.unescape(str(entry.get("title") or "")).strip()
        summary = html.unescape(re.sub(r"<[^>]+>", " ", str(entry.get("summary") or ""))).strip()
        if not title:
            return None

        if not self._is_relevant(title, summary, str(feed_def["key"])):
            return None

        published_at = self._parse_timestamp_dt(entry.get("published") or entry.get("updated"))
        if (datetime.now(timezone.utc) - published_at).total_seconds() > self.MAX_AGE_HOURS * 3600:
            return None

        title_for_score = title.lower()
        sentiment_score = macro_news_collector._score_headline(title_for_score)
        if abs(sentiment_score) < 0.08 and not any(
            word in title_for_score for word in (macro_news_collector.surge_keywords + macro_news_collector.plunge_keywords)
        ):
            sentiment_score = 0.0

        trigger_id = str(feed_def["trigger_id"])
        direction = macro_news_collector._determine_direction(title_for_score, sentiment_score, trigger_id)
        magnitude = macro_news_collector._determine_magnitude(title_for_score, sentiment_score)
        importance = float(feed_def["base_importance"])
        if magnitude == "extreme":
            importance = min(1.0, importance + 0.18)
        elif magnitude == "high":
            importance = min(1.0, importance + 0.1)
        elif magnitude == "medium":
            importance = min(1.0, importance + 0.05)

        thesis_horizon = self._classify_thesis_horizon(title, summary, importance)

        return {
            "trigger_id": trigger_id,
            "direction": direction,
            "magnitude": magnitude,
            "headline": financial_translator.translate_headline(title),
            "original_headline": title,
            "source_url": str(entry.get("link") or "").strip(),
            "publisher": str(feed_def["publisher"]),
            "sentiment_score": sentiment_score,
            "importance_score": round(importance, 2),
            "timestamp": published_at.isoformat(),
            "category": "global_news",
            "thesis_horizon": thesis_horizon,
        }

    def _classify_thesis_horizon(self, title: str, summary: str, importance: float) -> str:
        normalized = self._normalize_text(f"{title} {summary}")
        medium_term_keywords = (
            "inflation",
            "interest rate",
            "central bank",
            "tariff",
            "trade",
            "sanction",
            "budget",
            "growth",
            "recession",
            "earnings",
            "guidance",
            "oil",
            "gold",
            "bond yield",
            "credit",
        )
        if importance >= 0.82 or any(keyword in normalized for keyword in medium_term_keywords):
            return "medium_term"
        return "short_term"

    def _fetch_feed_sync(self, feed_def: dict[str, Any], limit: int) -> list[dict[str, Any]]:
        parsed = feedparser.parse(str(feed_def["url"]))
        items: list[dict[str, Any]] = []
        for entry in parsed.entries[: max(limit * 2, 10)]:
            normalized = self._normalize_entry(entry, feed_def)
            if normalized is None:
                continue
            items.append(normalized)
            if len(items) >= limit:
                break
        return items

    async def fetch_market_news(self, limit: int = 12) -> List[Dict]:
        logger.info("Public RSS market news fetch started")
        per_feed_limit = max(2, limit // max(len(self.FEEDS), 1) + 1)
        batches = await asyncio.gather(
            *(asyncio.to_thread(self._fetch_feed_sync, feed_def, per_feed_limit) for feed_def in self.FEEDS),
            return_exceptions=True,
        )

        items: list[dict[str, Any]] = []
        for batch in batches:
            if isinstance(batch, Exception):
                logger.warning("External RSS feed fetch failed: %s", batch)
                continue
            items.extend(batch)

        deduped: dict[Tuple[str, str], dict[str, Any]] = {}
        for item in items:
            key = (
                self._normalize_text(item.get("headline") or ""),
                (item.get("source_url") or "").strip().lower(),
            )
            current = deduped.get(key)
            if current is None or float(item.get("importance_score") or 0) > float(current.get("importance_score") or 0):
                deduped[key] = item

        ranked = sorted(
            deduped.values(),
            key=lambda item: (
                -float(item.get("importance_score") or 0),
                -abs(float(item.get("sentiment_score") or 0)),
                item.get("timestamp") or "",
            ),
            reverse=False,
        )
        ranked.reverse()
        return ranked[:limit]


external_news_rss_collector = ExternalNewsRSSCollector()
