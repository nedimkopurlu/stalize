import types
from datetime import datetime, timezone
from email.utils import format_datetime

import pytest

from app.services.external_news_rss import ExternalNewsRSSCollector


def _entry(**kwargs):
    return types.SimpleNamespace(**kwargs)


def _fresh_rfc2822():
    return format_datetime(datetime.now(timezone.utc))


def test_normalize_entry_filters_personal_finance_marketwatch_item():
    collector = ExternalNewsRSSCollector()
    feed_def = collector.FEEDS[0]

    item = collector._normalize_entry(
        {
            "title": "I’m planning to retire at 60. Should I sell my house?",
            "summary": "Personal finance decision",
            "link": "https://example.com/retire",
            "published": _fresh_rfc2822(),
        },
        feed_def,
    )

    assert item is None


def test_normalize_entry_keeps_macro_relevant_item():
    collector = ExternalNewsRSSCollector()
    feed_def = collector.FEEDS[0]

    item = collector._normalize_entry(
        {
            "title": "Jobless claims fall to lowest level since mid-May",
            "summary": "Labor market data and treasury yields move lower.",
            "link": "https://example.com/jobless",
            "published": _fresh_rfc2822(),
        },
        feed_def,
    )

    assert item is not None
    assert item["publisher"] == "Reuters"
    assert item["trigger_id"] == "bist100_index"
    assert item["thesis_horizon"] == "medium_term"


def test_normalize_entry_filters_investing_insider_filing_noise():
    collector = ExternalNewsRSSCollector()
    feed_def = next(item for item in collector.FEEDS if item["key"] == "investing_stock")

    item = collector._normalize_entry(
        {
            "title": "Netlist director Blake Welcher sells $75,000 in common stock",
            "summary": "",
            "link": "https://example.com/insider",
            "published": _fresh_rfc2822(),
        },
        feed_def,
    )

    assert item is None


@pytest.mark.asyncio
async def test_fetch_market_news_dedupes_same_item(monkeypatch):
    collector = ExternalNewsRSSCollector()

    def fake_parse(url):
        return types.SimpleNamespace(
            entries=[
                {
                    "title": "Dollar slips after U.S., Iran agree to more peace talks",
                    "summary": "Forex markets react.",
                    "link": "https://example.com/fx",
                    "published": _fresh_rfc2822(),
                }
            ]
        )

    monkeypatch.setattr("app.services.external_news_rss.feedparser.parse", fake_parse)

    items = await collector.fetch_market_news(limit=10)

    assert len(items) == 1
    assert items[0]["publisher"] in {"Investing", "MarketWatch", "Reuters", "CNBC", "Financial Times", "Yahoo Finance", "Bloomberg HT", "Ekonomim", "Dunya"}


def test_normalize_entry_filters_stale_items():
    collector = ExternalNewsRSSCollector()
    feed_def = collector.FEEDS[0]

    item = collector._normalize_entry(
        {
            "title": "Jobless claims fall to lowest level since mid-May",
            "summary": "Labor market data and treasury yields move lower.",
            "link": "https://example.com/jobless",
            "published": "Thu, 03 Jul 2025 12:36:00 GMT",
        },
        feed_def,
    )

    assert item is None
