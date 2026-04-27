"""Kanonik BIST100 evreni.

Bu dosya sembol, şirket adı, sektör ve BIST30 bayrağı için tek doğruluk kaynağıdır.
"""

from __future__ import annotations

from typing import Dict, List


BIST100_UNIVERSE: List[Dict[str, object]] = [
    {"symbol": "AEFES", "name": "Anadolu Efes", "sector": "İçecek", "is_bist30": False},
    {"symbol": "AGHOL", "name": "Anadolu Grubu Holding", "sector": "Holding", "is_bist30": False},
    {"symbol": "AKBNK", "name": "Akbank", "sector": "Banka", "is_bist30": True},
    {"symbol": "AKSA", "name": "Aksa", "sector": "Kimya", "is_bist30": False},
    {"symbol": "AKSEN", "name": "Aksa Enerji", "sector": "Enerji", "is_bist30": False},
    {"symbol": "ALARK", "name": "Alarko Holding", "sector": "Holding", "is_bist30": False},
    {"symbol": "ALTNY", "name": "Altınay Savunma", "sector": "Savunma", "is_bist30": False},
    {"symbol": "ANSGR", "name": "Anadolu Sigorta", "sector": "Sigorta", "is_bist30": False},
    {"symbol": "ARCLK", "name": "Arçelik", "sector": "Dayanıklı Tüketim", "is_bist30": True},
    {"symbol": "ASELS", "name": "Aselsan", "sector": "Savunma", "is_bist30": True},
    {"symbol": "ASTOR", "name": "Astor Enerji", "sector": "Elektrik Ekipmanları", "is_bist30": True},
    {"symbol": "BALSU", "name": "Balsu Gıda", "sector": "Gıda", "is_bist30": False},
    {"symbol": "BIMAS", "name": "BİM Mağazalar", "sector": "Perakende", "is_bist30": True},
    {"symbol": "BRSAN", "name": "Borusan Boru Sanayi", "sector": "Sanayi", "is_bist30": False},
    {"symbol": "BRYAT", "name": "Borusan Yatırım Pazarlama", "sector": "Yatırım", "is_bist30": False},
    {"symbol": "BSOKE", "name": "Batısöke Çimento", "sector": "Çimento", "is_bist30": False},
    {"symbol": "BTCIM", "name": "Batı Çimento", "sector": "Çimento", "is_bist30": False},
    {"symbol": "CANTE", "name": "Çan2 Termik", "sector": "Enerji", "is_bist30": False},
    {"symbol": "CCOLA", "name": "Coca Cola İçecek", "sector": "İçecek", "is_bist30": True},
    {"symbol": "CIMSA", "name": "Çimsa", "sector": "Çimento", "is_bist30": False},
    {"symbol": "CVKMD", "name": "CVK Maden", "sector": "Madencilik", "is_bist30": False},
    {"symbol": "CWENE", "name": "CW Enerji", "sector": "Enerji Teknolojileri", "is_bist30": False},
    {"symbol": "DAPGM", "name": "DAP Gayrimenkul", "sector": "Gayrimenkul", "is_bist30": False},
    {"symbol": "DOAS", "name": "Doğuş Otomotiv", "sector": "Otomotiv", "is_bist30": False},
    {"symbol": "DOHOL", "name": "Doğan Holding", "sector": "Holding", "is_bist30": False},
    {"symbol": "DSTKF", "name": "Destek Finans Faktoring", "sector": "Finansal Hizmetler", "is_bist30": False},
    {"symbol": "ECILC", "name": "Eczacıbaşı İlaç", "sector": "İlaç", "is_bist30": False},
    {"symbol": "EFOR", "name": "Efor Yatırım", "sector": "Yatırım", "is_bist30": False},
    {"symbol": "EKGYO", "name": "Emlak Konut GMYO", "sector": "Gayrimenkul", "is_bist30": True},
    {"symbol": "ENERY", "name": "Enerya Enerji", "sector": "Enerji", "is_bist30": False},
    {"symbol": "ENJSA", "name": "Enerjisa Enerji", "sector": "Enerji", "is_bist30": True},
    {"symbol": "ENKAI", "name": "Enka İnşaat", "sector": "İnşaat", "is_bist30": True},
    {"symbol": "EREGL", "name": "Ereğli Demir Çelik", "sector": "Demir Çelik", "is_bist30": True},
    {"symbol": "EUPWR", "name": "Europower Enerji", "sector": "Elektrik Ekipmanları", "is_bist30": False},
    {"symbol": "EUREN", "name": "Europen Endüstri", "sector": "Sanayi", "is_bist30": False},
    {"symbol": "FENER", "name": "Fenerbahçe Futbol", "sector": "Spor", "is_bist30": False},
    {"symbol": "FROTO", "name": "Ford Otosan", "sector": "Otomotiv", "is_bist30": True},
    {"symbol": "GARAN", "name": "Garanti Bankası", "sector": "Banka", "is_bist30": True},
    {"symbol": "GENIL", "name": "Gen İlaç", "sector": "İlaç", "is_bist30": False},
    {"symbol": "GESAN", "name": "Girişim Elektrik Sanayi", "sector": "Elektrik Ekipmanları", "is_bist30": False},
    {"symbol": "GLRMK", "name": "Gülermak Ağır Sanayi", "sector": "İnşaat", "is_bist30": False},
    {"symbol": "GRSEL", "name": "Gür-Sel Turizm Taşımacılık", "sector": "Ulaştırma", "is_bist30": False},
    {"symbol": "GRTHO", "name": "Graintürk Holding", "sector": "Holding", "is_bist30": False},
    {"symbol": "GSRAY", "name": "Galatasaray Sportif", "sector": "Spor", "is_bist30": False},
    {"symbol": "GUBRF", "name": "Gübre Fabrikaları", "sector": "Kimya", "is_bist30": True},
    {"symbol": "HALKB", "name": "T. Halk Bankası", "sector": "Banka", "is_bist30": True},
    {"symbol": "HEKTS", "name": "Hektaş", "sector": "Tarım Kimyasalları", "is_bist30": False},
    {"symbol": "ISCTR", "name": "İş Bankası (C)", "sector": "Banka", "is_bist30": True},
    {"symbol": "ISMEN", "name": "İş Yatırım Menkul Değerler", "sector": "Aracı Kurum", "is_bist30": False},
    {"symbol": "IZENR", "name": "İzdemir Enerji", "sector": "Enerji", "is_bist30": False},
    {"symbol": "KCHOL", "name": "Koç Holding", "sector": "Holding", "is_bist30": True},
    {"symbol": "KLRHO", "name": "Kiler Holding", "sector": "Holding", "is_bist30": False},
    {"symbol": "KONTR", "name": "Kontrolmatik Teknoloji", "sector": "Teknoloji", "is_bist30": False},
    {"symbol": "KRDMD", "name": "Kardemir (D)", "sector": "Demir Çelik", "is_bist30": True},
    {"symbol": "KTLEV", "name": "Katılımevim Tasarruf Finansman", "sector": "Finansal Hizmetler", "is_bist30": False},
    {"symbol": "KUYAS", "name": "Kuyaş Yatırım", "sector": "Yatırım", "is_bist30": False},
    {"symbol": "MAGEN", "name": "Margün Enerji", "sector": "Enerji", "is_bist30": False},
    {"symbol": "MAVI", "name": "Mavi Giyim", "sector": "Perakende", "is_bist30": False},
    {"symbol": "MGROS", "name": "Migros Ticaret", "sector": "Perakende", "is_bist30": True},
    {"symbol": "MIATK", "name": "Mia Teknoloji", "sector": "Teknoloji", "is_bist30": False},
    {"symbol": "MPARK", "name": "MLP Sağlık", "sector": "Sağlık", "is_bist30": False},
    {"symbol": "OBAMS", "name": "Oba Makarnacılık", "sector": "Gıda", "is_bist30": False},
    {"symbol": "ODAS", "name": "Odaş Elektrik", "sector": "Enerji", "is_bist30": False},
    {"symbol": "OTKAR", "name": "Otokar", "sector": "Savunma", "is_bist30": False},
    {"symbol": "OYAKC", "name": "Oyak Çimento", "sector": "Çimento", "is_bist30": False},
    {"symbol": "PAHOL", "name": "Pasifik Holding", "sector": "Holding", "is_bist30": False},
    {"symbol": "PASEU", "name": "Pasifik Eurasia Lojistik", "sector": "Lojistik", "is_bist30": False},
    {"symbol": "PATEK", "name": "Pasifik Teknoloji", "sector": "Teknoloji", "is_bist30": False},
    {"symbol": "PETKM", "name": "Petkim", "sector": "Petrokimya", "is_bist30": True},
    {"symbol": "PGSUS", "name": "Pegasus", "sector": "Havacılık", "is_bist30": True},
    {"symbol": "PSGYO", "name": "Pasifik GMYO", "sector": "Gayrimenkul", "is_bist30": False},
    {"symbol": "QUAGR", "name": "Qua Granite Hayal Yapı", "sector": "Yapı Malzemeleri", "is_bist30": False},
    {"symbol": "RALYH", "name": "Ral Yatırım Holding", "sector": "Holding", "is_bist30": False},
    {"symbol": "REEDR", "name": "Reeder Teknoloji", "sector": "Teknoloji", "is_bist30": False},
    {"symbol": "SAHOL", "name": "Sabancı Holding", "sector": "Holding", "is_bist30": True},
    {"symbol": "SARKY", "name": "Sarkuysan", "sector": "Sanayi", "is_bist30": False},
    {"symbol": "SASA", "name": "Sasa Polyester", "sector": "Petrokimya", "is_bist30": True},
    {"symbol": "SISE", "name": "Şişe Cam", "sector": "Cam", "is_bist30": True},
    {"symbol": "SKBNK", "name": "Şekerbank", "sector": "Banka", "is_bist30": False},
    {"symbol": "SOKM", "name": "Şok Marketler Ticaret", "sector": "Perakende", "is_bist30": False},
    {"symbol": "TABGD", "name": "Tab Gıda", "sector": "Restoran", "is_bist30": False},
    {"symbol": "TAVHL", "name": "TAV Havalimanları", "sector": "Havacılık", "is_bist30": True},
    {"symbol": "TCELL", "name": "Turkcell", "sector": "Telekom", "is_bist30": True},
    {"symbol": "THYAO", "name": "Türk Hava Yolları", "sector": "Havacılık", "is_bist30": True},
    {"symbol": "TKFEN", "name": "Tekfen Holding", "sector": "İnşaat", "is_bist30": False},
    {"symbol": "TOASO", "name": "Tofaş Oto. Fab.", "sector": "Otomotiv", "is_bist30": True},
    {"symbol": "TRALT", "name": "Türk Altın İşletmeleri", "sector": "Madencilik", "is_bist30": False},
    {"symbol": "TRENJ", "name": "TR Doğal Enerji", "sector": "Enerji", "is_bist30": False},
    {"symbol": "TRMET", "name": "TR Anadolu Metal Madencilik", "sector": "Madencilik", "is_bist30": False},
    {"symbol": "TSKB", "name": "T.S.K.B.", "sector": "Banka", "is_bist30": False},
    {"symbol": "TTKOM", "name": "Türk Telekom", "sector": "Telekom", "is_bist30": False},
    {"symbol": "TUKAS", "name": "Tukaş", "sector": "Gıda", "is_bist30": False},
    {"symbol": "TUPRS", "name": "Tüpraş", "sector": "Enerji", "is_bist30": True},
    {"symbol": "TUREX", "name": "Tureks Turizm Taşımacılık", "sector": "Ulaştırma", "is_bist30": False},
    {"symbol": "TURSG", "name": "Türkiye Sigorta", "sector": "Sigorta", "is_bist30": False},
    {"symbol": "ULKER", "name": "Ülker Bisküvi", "sector": "Gıda", "is_bist30": False},
    {"symbol": "VAKBN", "name": "Vakıflar Bankası", "sector": "Banka", "is_bist30": True},
    {"symbol": "VESTL", "name": "Vestel", "sector": "Dayanıklı Tüketim", "is_bist30": False},
    {"symbol": "YKBNK", "name": "Yapı ve Kredi Bankası", "sector": "Banka", "is_bist30": True},
    {"symbol": "ZOREN", "name": "Zorlu Enerji", "sector": "Enerji", "is_bist30": False},
]


def get_bist100_symbols() -> List[str]:
    return [item["symbol"] for item in BIST100_UNIVERSE]


def get_bist100_company_map() -> Dict[str, str]:
    return {item["symbol"]: item["name"] for item in BIST100_UNIVERSE}


def get_bist100_sector_map() -> Dict[str, str]:
    return {item["symbol"]: item["sector"] for item in BIST100_UNIVERSE}


def get_bist30_symbols() -> List[str]:
    return [item["symbol"] for item in BIST100_UNIVERSE if item["is_bist30"]]
