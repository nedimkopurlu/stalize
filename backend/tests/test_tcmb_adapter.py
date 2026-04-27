from app.services.tcmb_adapter import TCMBAdapter


def test_parse_atom_entries_and_find_latest_interest_rate_entry():
    xml = """<?xml version="1.0" encoding="utf-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>Genel Kurul Duyurusu</title>
        <link rel="alternate" type="text/html" href="http://www.tcmb.gov.tr/other"></link>
        <published>24 Nis 2026 14:00:00</published>
        <updated>24 Nis 2026 14:00:01</updated>
      </entry>
      <entry>
        <title>Faiz Oranlarına İlişkin Basın Duyurusu (2026-17)</title>
        <link rel="alternate" type="text/html" href="http://www.tcmb.gov.tr/faiz"></link>
        <published>22 Nis 2026 14:00:00</published>
        <updated>22 Nis 2026 14:00:01</updated>
      </entry>
    </feed>"""

    adapter = TCMBAdapter()
    entries = adapter._parse_atom_entries(xml)
    picked = adapter._find_latest_interest_rate_entry(xml)

    assert len(entries) == 2
    assert entries[0]["url"] == "https://www.tcmb.gov.tr/other"
    assert picked is not None
    assert picked["title"] == "Faiz Oranlarına İlişkin Basın Duyurusu (2026-17)"
    assert picked["url"] == "https://www.tcmb.gov.tr/faiz"


def test_parse_policy_rate_extracts_repo_rate():
    html = """
    <p>Para Politikası Kurulu, politika faizi olan bir hafta vadeli repo ihale
    faiz oranının yüzde 37'de sabit tutulmasına karar vermiştir.</p>
    """

    adapter = TCMBAdapter()
    payload = adapter._parse_policy_rate(html)

    assert payload is not None
    assert payload["rate"] == 37.0
