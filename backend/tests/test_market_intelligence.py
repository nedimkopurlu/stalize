import pytest

from app.services.market_intelligence import MarketIntelligenceService


@pytest.mark.asyncio
async def test_unified_feed_prefers_higher_priority_source_on_duplicate_headline(monkeypatch):
    service = MarketIntelligenceService()

    async def fake_macro():
        return [
            {
                "headline": "TCMB Politika Faiz Oranı: 37%",
                "source_url": "",
                "publisher": "Yahoo Finance",
                "sentiment_score": -0.1,
                "importance_score": 0.4,
                "timestamp": "2026-04-24T10:00:00+00:00",
                "thesis_horizon": "short_term",
            }
        ]

    async def fake_kap(limit=20):
        return []

    async def fake_official(limit=20):
        return [
            {
                "headline": "TCMB Politika Faiz Oranı: 37%",
                "source_url": "",
                "publisher": "TCMB",
                "sentiment_score": 0.0,
                "importance_score": 0.95,
                "timestamp": "2026-04-24T10:05:00+00:00",
                "thesis_horizon": "medium_term",
            }
        ]

    async def fake_external(limit=20):
        return []

    monkeypatch.setattr("app.services.market_intelligence.macro_news_collector.fetch_real_events", fake_macro)
    monkeypatch.setattr("app.services.market_intelligence.kap_parser.get_recent_feed", fake_kap)
    monkeypatch.setattr(service, "get_official_feed", fake_official)
    monkeypatch.setattr("app.services.market_intelligence.external_news_rss_collector.fetch_market_news", fake_external)

    feed = await service.get_unified_feed(limit=10)

    assert len(feed) == 1
    assert feed[0]["publisher"] == "TCMB"
    assert feed[0]["thesis_horizon"] == "medium_term"


@pytest.mark.asyncio
async def test_source_rank_handles_turkish_source_names():
    service = MarketIntelligenceService()

    assert service._source_rank("Borsa İstanbul") < service._source_rank("Yahoo Finance")


@pytest.mark.asyncio
async def test_official_feed_filters_irrelevant_hmb_items_and_unescapes_headlines(monkeypatch):
    service = MarketIntelligenceService()

    class FakeNews:
        def __init__(self, title, source):
            self.title = title
            self.source = source
            self.url = "https://example.com"
            self.sentiment_score = 0.0
            self.importance_score = 0.6
            self.published_at = None
            self.category = "fiscal"

    class FakeResult:
        def all(self):
            return [
                (FakeNews("Basın Duyurusu &#8211; 12.04.2026", "HMB"), None),
                (FakeNews("Hazine ve Maliye Uzman Yardımcılığı Giriş Sınavına İlişkin Duyuru", "HMB"), None),
            ]

    class FakeDB:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def execute(self, _stmt):
            return FakeResult()

    monkeypatch.setattr("app.services.market_intelligence.AsyncSessionLocal", lambda: FakeDB())

    feed = await service.get_official_feed(limit=10)

    assert len(feed) == 1
    assert feed[0]["headline"] == "Basın Duyurusu – 12.04.2026"


@pytest.mark.asyncio
async def test_overview_tracks_horizon_summary(monkeypatch):
    service = MarketIntelligenceService()

    async def fake_feed(limit=10):
        return [
            {"publisher": "KAP", "thesis_horizon": "medium_term"},
            {"publisher": "Reuters", "thesis_horizon": "short_term"},
            {"publisher": "TCMB", "thesis_horizon": "medium_term"},
        ]

    async def fake_scenarios(limit=10):
        return []

    monkeypatch.setattr(service, "get_unified_feed", fake_feed)
    monkeypatch.setattr(service, "get_unified_scenarios", fake_scenarios)

    overview = await service.get_overview(limit=10)

    assert overview["horizon_summary"]["medium_term"] == 2
    assert overview["horizon_summary"]["short_term"] == 1


@pytest.mark.asyncio
async def test_unified_feed_filters_stale_company_items(monkeypatch):
    service = MarketIntelligenceService()

    async def fake_macro():
        return []

    async def fake_kap(limit=20):
        return [
            {
                "headline": "Eski KAP bildirimi",
                "source_url": "https://www.kap.org.tr/tr/Bildirim/1",
                "publisher": "KAP",
                "sentiment_score": 0.7,
                "importance_score": 0.95,
                "timestamp": "2026-04-15T10:00:00+00:00",
                "category": "company",
                "thesis_horizon": "short_term",
            }
        ]

    async def fake_official(limit=20):
        return [
            {
                "headline": "TUIK TÜFE Enflasyon: Yıllık %30.9",
                "source_url": "",
                "publisher": "TUIK",
                "sentiment_score": 0.0,
                "importance_score": 0.95,
                "timestamp": "2026-04-24T10:05:00+00:00",
                "category": "macro",
                "thesis_horizon": "medium_term",
            }
        ]

    async def fake_external(limit=20):
        return []

    monkeypatch.setattr("app.services.market_intelligence.macro_news_collector.fetch_real_events", fake_macro)
    monkeypatch.setattr("app.services.market_intelligence.kap_parser.get_recent_feed", fake_kap)
    monkeypatch.setattr(service, "get_official_feed", fake_official)
    monkeypatch.setattr("app.services.market_intelligence.external_news_rss_collector.fetch_market_news", fake_external)

    feed = await service.get_unified_feed(limit=10)

    assert len(feed) == 1
    assert feed[0]["publisher"] == "TUIK"
