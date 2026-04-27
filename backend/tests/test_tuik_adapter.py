from app.services.tuik_adapter import TUIKAdapter


def test_fetch_bulletin_cards_parses_title_metric_summary_and_date():
    html = """
    <div class="swiper-slide">
      <a href="https://veriportali.tuik.gov.tr/tr/press/58111">
        <div class="card">
          <div class="card-header">
            <date>03 Nisan 2026</date>
            <span class="text-tuik-dark font-weight-bold">Tüketici Fiyat Endeksi, Mart 2026</span>
            <p class="text-tuik-dark">%30,87(yıl)</p>
          </div>
          <div class="card-body">
            <div class="row">Tüketici fiyat endeksi (TÜFE) yıllık %30,87 arttı, aylık %1,94 arttı</div>
          </div>
        </div>
      </a>
    </div>
    """

    adapter = TUIKAdapter()
    cards = adapter._parse_bulletin_cards(html)

    assert len(cards) == 1
    assert cards[0]["title"] == "Tüketici Fiyat Endeksi, Mart 2026"
    assert cards[0]["metric"] == "%30,87(yıl)"
    assert cards[0]["summary"].startswith("Tüketici fiyat endeksi")
    assert cards[0]["published_on"] == "03 Nisan 2026"


def test_parse_cpi_reads_annual_and_monthly_values():
    adapter = TUIKAdapter()
    payload = adapter._parse_cpi(
        "Tüketici fiyat endeksi (TÜFE) yıllık %30,87 arttı, aylık %1,94 arttı"
    )

    assert payload is not None
    assert payload["inflation_rate_annual"] == 30.87
    assert payload["inflation_rate_monthly"] == 1.94


def test_normalize_text_handles_turkish_characters():
    adapter = TUIKAdapter()
    assert adapter._normalize_text("Tüketici Fiyat Endeksi") == "tuketici fiyat endeksi"


def test_parse_popular_indicators_extracts_core_cards():
    html = """
    <div class="chartcard" onclick="gostergeLink('__TUKETICI_FIYAT_ENDEKSI__', '58295','Tuketici-Fiyat-Endeksi-Mart-2026-58295');">
      <div class="chartheader"><span>Tüketici Fiyat Endeksi-Yıllık (%)</span></div>
      <div class="chartdiv"><span>2026/3 (Ay)</span></div>
      <div class="chartfooter">30,87</div>
    </div>
    <div class="chartcard" onclick="gostergeLink('__ISSIZLIK_ORANI_ARINDIRILMIS__', '57997','Isgucu-Istatistikleri-Subat-2026-57997');">
      <div class="chartheader"><span>İşsizlik Oranı (%)</span></div>
      <div class="chartdiv"><span>2026/2 (Ay)</span></div>
      <div class="chartfooter">8,5</div>
    </div>
    """

    adapter = TUIKAdapter()
    payload = adapter._parse_popular_indicators(html)

    assert len(payload) == 2
    assert payload[0]["title"] == "Tüketici Fiyat Endeksi-Yıllık (%)"
    assert payload[0]["period"] == "2026/3 (Ay)"
    assert payload[0]["value"] == "30,87"
    assert payload[0]["url"].endswith("/tr/press/58295")
