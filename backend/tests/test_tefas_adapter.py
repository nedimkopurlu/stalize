from app.services.tefas_adapter import TefasAdapter


def test_parse_fund_detail_extracts_metrics():
    html = """
    <html>
      <head><title>AFT - Ak Portföy Yeni Teknolojiler Yabancı Hisse Senedi Fonu</title></head>
      <body>
        <h1>AFT - Ak Portföy Yeni Teknolojiler Yabancı Hisse Senedi Fonu</h1>
        <div>Son Fiyat: 0,123456</div>
        <div>Günlük Getiri: 1,25</div>
        <div>Yatırımcı Sayısı: 12543</div>
        <div>Risk Değeri: 6</div>
        <div>1 Ay: 4,22</div>
        <div>3 Ay: 8,40</div>
        <div>6 Ay: 12,55</div>
        <div>1 Yıl: 31,70</div>
      </body>
    </html>
    """
    adapter = TefasAdapter()

    result = adapter._parse_fund_detail(html, "AFT", "https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod=AFT")

    assert result is not None
    assert result["fund_code"] == "AFT"
    assert "Ak Portföy" in result["fund_name"]
    assert result["price"] == 0.123456
    assert result["daily_change_pct"] == 1.25
    assert result["investor_count"] == 12543
    assert result["risk_value"] == 6
    assert result["one_month_return_pct"] == 4.22
    assert result["three_month_return_pct"] == 8.40
    assert result["six_month_return_pct"] == 12.55
    assert result["one_year_return_pct"] == 31.70


def test_parse_fund_detail_returns_none_when_code_missing():
    adapter = TefasAdapter()

    result = adapter._parse_fund_detail("<html><body>Veri yok</body></html>", "AFT", "https://example.com")

    assert result is None


def test_normalize_fund_universe_maps_rows():
    adapter = TefasAdapter()

    payload = {
        "recordsTotal": 2,
        "data": [
            {
                "FONKODU": "AFT",
                "FONUNVAN": "AK PORTFÖY YENİ TEKNOLOJİLER YABANCI HİSSE SENEDİ FONU",
                "FONTURACIKLAMA": "Hisse Senedi Şemsiye Fonu",
                "GETIRI1A": 4.22,
                "GETIRI3A": 8.4,
                "GETIRI6A": 12.55,
                "GETIRIYB": 11.1,
                "GETIRI1Y": 31.7,
                "GETIRI3Y": 120.0,
                "GETIRI5Y": None,
            }
        ],
    }

    result = adapter._normalize_fund_universe(payload, fund_type="YAT")

    assert result["fund_type"] == "YAT"
    assert result["total"] == 2
    assert result["count"] == 1
    assert result["items"][0]["fund_code"] == "AFT"
    assert result["items"][0]["detail_url"].endswith("FonAnaliz.aspx?FonKod=AFT")
