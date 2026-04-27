"""
Tests for FOND-01: KAP mock data removal and feedparser hard import.

Three behaviors tested:
1. test_no_mock_method: KAPParser has no _generate_mock_announcements attribute
2. test_startup_error_without_feedparser: hard import of feedparser fails when missing
3. test_kap_unreachable_returns_empty: when feedparser.parse() raises, fetch_latest_announcements returns []
"""
import sys
import pytest
from unittest.mock import patch


def test_no_mock_method():
    """_generate_mock_announcements must not exist on KAPParser after FOND-01 fix."""
    from app.services.kap_parser import KAPParser
    assert not hasattr(KAPParser, "_generate_mock_announcements"), (
        "KAPParser._generate_mock_announcements still exists — mock code was not deleted"
    )


def test_startup_error_without_feedparser(monkeypatch):
    """
    Simulates feedparser missing by patching the import.
    After FOND-01: importing kap_parser with feedparser absent must raise ImportError or ModuleNotFoundError
    (hard import at module top, not try/except).
    """
    import importlib

    # Remove feedparser from sys.modules to simulate missing package
    sys.modules.pop("feedparser", None)
    monkeypatch.setitem(sys.modules, "feedparser", None)  # type: ignore

    with pytest.raises((ImportError, ModuleNotFoundError, AttributeError)):
        import app.services.kap_parser as kap_mod  # noqa: F401
        importlib.reload(kap_mod)


@pytest.mark.asyncio
async def test_kap_unreachable_returns_empty(monkeypatch):
    """
    When feedparser.parse() raises an exception (KAP temporarily down),
    fetch_latest_announcements must return [] with a WARNING log — not mock data.
    """
    import feedparser
    from app.services.kap_parser import KAPParser

    parser = KAPParser()

    def raise_network_error(url):
        raise ConnectionError("KAP RSS unreachable")

    monkeypatch.setattr(feedparser, "parse", raise_network_error)

    result = await parser.fetch_latest_announcements()
    assert result == [], f"Expected [], got {result!r} — mock data is still being returned"


def test_kap_event_classification_and_scoring_are_more_specific():
    from app.services.kap_parser import KAPParser

    parser = KAPParser()

    cases = [
        ("THYAO Nakit Kar Payı Dağıtımına İlişkin Yönetim Kurulu Kararı", "dividend", "positive"),
        ("ASELS Bedelsiz Sermaye Artırımı Hakkında", "bonus_issue", "positive"),
        ("KONTR Bedelli Sermaye Artırımı Başvurusu", "rights_issue", "negative"),
        ("CWENE Yeni İş İlişkisi ve Sözleşme İmzalanması", "contract", "positive"),
        ("ODAS İhale Sonucu", "tender", "positive"),
        ("AKBNK Kredi Derecelendirme Notu Güncellemesi", "credit_rating", "neutral"),
        ("HEKTS İdari Para Cezası Hakkında", "legal", "negative"),
        ("ENKAI Tahvil İhracı ve Finansman Süreci Hakkında", "financing", "neutral"),
        ("SAHOL Pay Satış İşlemine İlişkin Açıklama", "share_sale", "negative"),
        ("TOASO Birleşme İşlemine İlişkin Duyuru", "merger", "positive"),
    ]

    for title, event_type, label in cases:
        detected = parser._classify_event(title)
        analysis = parser._analyze_announcement(title, detected)
        assert detected == event_type
        assert analysis["sentiment_label"] == label


def test_kap_event_priority_prefers_dividend_before_generic_earnings():
    from app.services.kap_parser import KAPParser

    parser = KAPParser()
    title = "THYAO Kar Payı Dağıtım Teklifi ve Finansal Sonuç Bildirimi"

    assert parser._classify_event(title) == "dividend"


def test_kap_thesis_profile_marks_medium_term_events():
    from app.services.kap_parser import KAPParser

    parser = KAPParser()
    analysis = parser._analyze_announcement(
        "ASELS Bedelsiz Sermaye Artırımı Hakkında",
        "bonus_issue",
    )

    assert analysis["thesis_horizon"] == "medium_term"
    assert analysis["thesis_weight"] >= 0.85
