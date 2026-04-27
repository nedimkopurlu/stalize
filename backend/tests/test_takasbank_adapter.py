from app.services.official_news_ingest import _parse_tr_date
from app.services.takasbank_adapter import TakasbankAdapter


def test_parse_takasbank_announcements_extracts_cards():
    html = """
    <html>
      <body>
        <div class="notifications-list">
          <div class="notification media">
            <div class="date">
              <div class="day">16</div>
              <div class="month">Nis</div>
            </div>
            <div class="media-body">
              <div class="category">Teminat İzleme</div>
              <div class="text">
                <a href="/documents/file/Takasbank_Announcement/2144-example.pdf">
                  Risk Parametrelerinin Güncellenmesi Hk.
                </a>
              </div>
            </div>
          </div>
          <div class="notification media">
            <div class="date">
              <div class="day">15</div>
              <div class="month">Nis</div>
            </div>
            <div class="media-body">
              <div class="category">Kurumsal Mimari</div>
              <div class="text">
                <a href="/documents/file/Takasbank_Announcement/2143-example.pdf">
                  Takasbank Olağanüstü Durum Sistemleri Duyurusu
                </a>
              </div>
            </div>
          </div>
        </div>
      </body>
    </html>
    """
    adapter = TakasbankAdapter()

    result = adapter._parse_announcements(html, limit=10)

    assert len(result) == 2
    assert result[0]["published_on"] == "16 Nis"
    assert result[0]["category"] == "Teminat İzleme"
    assert result[0]["headline"] == "Risk Parametrelerinin Güncellenmesi Hk."
    assert result[0]["url"] == "https://www.takasbank.com.tr/documents/file/Takasbank_Announcement/2144-example.pdf"


def test_parse_takasbank_announcements_deduplicates_and_limits():
    html = """
    <html>
      <body>
        <div class="notifications-list">
          <div class="notification media">
            <div class="date"><div class="day">16</div><div class="month">Nis</div></div>
            <div class="text"><a href="/docs/a.pdf">Aynı Duyuru</a></div>
          </div>
          <div class="notification media">
            <div class="date"><div class="day">16</div><div class="month">Nis</div></div>
            <div class="text"><a href="/docs/a.pdf">Aynı Duyuru</a></div>
          </div>
          <div class="notification media">
            <div class="date"><div class="day">15</div><div class="month">Nis</div></div>
            <div class="text"><a href="/docs/b.pdf">İkinci Duyuru</a></div>
          </div>
        </div>
      </body>
    </html>
    """
    adapter = TakasbankAdapter()

    result = adapter._parse_announcements(html, limit=1)

    assert len(result) == 1
    assert result[0]["headline"] == "Aynı Duyuru"


def test_parse_tr_date_supports_takasbank_month_abbreviations():
    published_at = _parse_tr_date("16 Nis")

    assert published_at is not None
    assert published_at.month == 4
    assert published_at.day == 16
