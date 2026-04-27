from app.services.hmb_adapter import HMBAdapter


def test_parse_hmb_publications_extracts_relevant_links():
    html = """
    <html>
      <body>
        <div class="announcement">
          <span>15.04.2026</span>
          <a href="/uploads/2026/04/mart-2026-butce-gerceklesmeleri.pdf">
            Mart 2026 Merkezi Yonetim Butce Gerceklesmeleri
          </a>
        </div>
        <div class="announcement">
          <span>10.04.2026</span>
          <a href="/uploads/2026/04/ic-borclanma-stratejisi.xlsx">
            Nisan-Haziran 2026 Ic Borclanma Stratejisi
          </a>
        </div>
        <div class="announcement">
          <a href="/kurumsal/hakkimizda">Kurumsal</a>
        </div>
      </body>
    </html>
    """

    adapter = HMBAdapter()
    result = adapter._parse_publications(html, limit=5)

    assert len(result) == 2
    assert result[0]["category"] == "butce"
    assert result[0]["published_on"] == "15.04.2026"
    assert result[0]["url"] == "https://www.hmb.gov.tr/uploads/2026/04/mart-2026-butce-gerceklesmeleri.pdf"
    assert result[1]["category"] == "borclanma"


def test_parse_hmb_publications_deduplicates_and_limits():
    html = """
    <html>
      <body>
        <a href="/files/butce.pdf">2026 Butce Sunumu</a>
        <a href="/files/butce.pdf">2026 Butce Sunumu</a>
        <a href="/files/borclanma.pdf">2026 Borclanma Programi</a>
      </body>
    </html>
    """

    adapter = HMBAdapter()
    result = adapter._parse_publications(html, limit=1)

    assert len(result) == 1
    assert result[0]["title"] == "2026 Butce Sunumu"


def test_normalize_api_post_unescapes_entities_and_filters_non_market_posts():
    adapter = HMBAdapter()

    irrelevant = adapter._normalize_api_post(
        {
            "title": {"rendered": "Hazine ve Maliye Uzman Yard&#305;mc&#305;l&#305;&#287;&#305; Giri&#351; S&#305;nav&#305;"},
            "excerpt": {"rendered": "<p>Basvuru takvimi aciklandi.</p>"},
            "link": "https://api.hmb.gov.tr/2026/04/13/example/",
            "date": "2026-04-13T09:00:00",
        }
    )
    assert irrelevant is None

    relevant = adapter._normalize_api_post(
        {
            "title": {"rendered": "Bas&#305;n Duyurusu &#8211; 12.04.2026"},
            "excerpt": {"rendered": "<p>Hazine nakit ger&#231;ekle&#351;meleri ve kamu finansmani gelismeleri.</p>"},
            "link": "https://api.hmb.gov.tr/2026/04/12/example/",
            "date": "2026-04-12T09:00:00",
        }
    )

    assert relevant is not None
    assert relevant["title"] == "Basın Duyurusu – 12.04.2026"
