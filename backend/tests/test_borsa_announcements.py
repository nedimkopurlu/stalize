from app.services.borsa_announcements import BorsaAnnouncementsAdapter
from app.services.official_news_ingest import _parse_tr_date


def test_parse_borsa_announcements_extracts_latest_rows():
    html = """
    <html>
      <body>
        <div>17 Nisan 2026 BIST Temettü ve BIST Temettü 25 Endeksleri Dönemsel Değişiklikleri</div>
        <div>10 Nisan 2026 LSEG Sürdürülebilirlik Değerleme Metodolojisinin Yenilenmesi Hakkında Duyuru</div>
        <div>03 Nisan 2026 BIST Geri Alım Endeksi Dönemsel Değişiklikleri</div>
      </body>
    </html>
    """
    adapter = BorsaAnnouncementsAdapter()

    result = adapter._parse_announcements(html, limit=2)

    assert len(result) == 2
    assert result[0]["published_on"] == "17 Nisan 2026"
    assert "BIST Temettü" in result[0]["headline"]
    assert result[1]["published_on"] == "10 Nisan 2026"


def test_parse_borsa_announcements_deduplicates_rows():
    html = """
    <html>
      <body>
        <div>17 Nisan 2026 BIST Temettü ve BIST Temettü 25 Endeksleri Dönemsel Değişiklikleri</div>
        <div>17 Nisan 2026 BIST Temettü ve BIST Temettü 25 Endeksleri Dönemsel Değişiklikleri</div>
      </body>
    </html>
    """
    adapter = BorsaAnnouncementsAdapter()

    result = adapter._parse_announcements(html, limit=10)

    assert len(result) == 1


def test_parse_tr_date_supports_turkish_months():
    published_at = _parse_tr_date("17 Nisan 2026")

    assert published_at is not None
    assert published_at.year == 2026
    assert published_at.month == 4
    assert published_at.day == 17
