import types
from datetime import datetime, timezone
from email.utils import format_datetime

import pytest

from app.services.external_news_rss import ExternalNewsRSSCollector


def _entry(**kwargs):
    return types.SimpleNamespace(**kwargs)


def _fresh_rfc2822():
    return format_datetime(datetime.now(timezone.utc))


def test_normalize_entry_filters_non_market_item():
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
            "title": "Borsa İstanbul günü rekor seviyeden tamamladı",
            "summary": "BIST 100 endeksi bankacılık hisseleri öncülüğünde yükseldi.",
            "link": "https://news.google.com/rss/articles/test",
            "published": _fresh_rfc2822(),
        },
        feed_def,
    )

    assert item is not None
    assert item["publisher"] == "Bloomberg HT"
    assert item["trigger_id"] == "bist100_index"
    assert item["thesis_horizon"] == "medium_term"


def test_normalize_entry_filters_personnel_notice_noise():
    collector = ExternalNewsRSSCollector()
    feed_def = collector.FEEDS[0]

    item = collector._normalize_entry(
        {
            "title": "Bakanlık personel alımı için giriş sınavı duyurdu",
            "summary": "",
            "link": "https://news.google.com/rss/articles/personel",
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
                    "title": "Borsa İstanbul bankacılık hisseleriyle yükseldi",
                    "summary": "BIST 100 endeksi gün içinde güçlü seyretti.",
                    "link": "https://news.google.com/rss/articles/bist",
                    "published": _fresh_rfc2822(),
                }
            ]
        )

    monkeypatch.setattr("app.services.external_news_rss.feedparser.parse", fake_parse)

    items = await collector.fetch_market_news(limit=10)

    assert len(items) == 1
    assert items[0]["publisher"] in {"Bloomberg HT", "Ekonomim", "Dünya", "CNBC-e", "Bigpara", "A Para", "Borsa Gündem", "Finans Gündem", "Para Analiz"}


def test_normalize_entry_filters_stale_items():
    collector = ExternalNewsRSSCollector()
    feed_def = collector.FEEDS[0]

    item = collector._normalize_entry(
        {
            "title": "Borsa İstanbul günü yükselişle tamamladı",
            "summary": "BIST 100 endeksi pozitif kapandı.",
            "link": "https://news.google.com/rss/articles/stale",
            "published": "Thu, 03 Jul 2025 12:36:00 GMT",
        },
        feed_def,
    )

    assert item is None
