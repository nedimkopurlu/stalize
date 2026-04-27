from app.services.mkk_adapter import MKKAdapter


def test_parse_bulletins_extracts_pdf_entries():
    html = """
    <html>
      <body>
        <a href="/sites/default/files/2026-04/MKK-Aylik-Piyasa-Bulteni-Mart-2026.pdf">
          MKK Aylık Piyasa Bülteni Mart 2026
        </a>
        <a href="/sites/default/files/2026-03/MKK-Aylik-Piyasa-Bulteni-Subat-2026.pdf">
          MKK Aylık Piyasa Bülteni Şubat 2026
        </a>
        <a href="/sites/default/files/2026-03/baska-dokuman.pdf">Başka Doküman</a>
      </body>
    </html>
    """
    adapter = MKKAdapter()

    result = adapter._parse_bulletins(html, limit=5)

    assert len(result) == 2
    assert result[0]["source"] == "MKK"
    assert result[0]["period"] == "Mart 2026"
    assert result[0]["url"] == "https://www.mkk.com.tr/sites/default/files/2026-04/MKK-Aylik-Piyasa-Bulteni-Mart-2026.pdf"
    assert result[1]["period"] == "Şubat 2026"


def test_parse_bulletins_respects_limit_and_deduplicates():
    html = """
    <html>
      <body>
        <a href="/files/MKK-Aylik-Piyasa-Bulteni-Ocak-2026.pdf">MKK Aylık Piyasa Bülteni Ocak 2026</a>
        <a href="/files/MKK-Aylik-Piyasa-Bulteni-Ocak-2026.pdf">MKK Aylık Piyasa Bülteni Ocak 2026</a>
        <a href="/files/MKK-Aylik-Piyasa-Bulteni-Aralik-2025.pdf">MKK Aylık Piyasa Bülteni Aralık 2025</a>
      </body>
    </html>
    """
    adapter = MKKAdapter()

    result = adapter._parse_bulletins(html, limit=1)

    assert len(result) == 1
    assert result[0]["period"] == "Ocak 2026"
