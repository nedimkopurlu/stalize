import logging
import re

logger = logging.getLogger(__name__)

class FinancialTranslator:
    """
    Stalize finansal terim çeviri motoru.
    Finansal terimleri ve haber başlıklarını Türkçeye çevirmek için tasarlanmış özel motor.
    """

    def __init__(self):
        # Önemli finansal anahtar kelimelerin birebir karşılıkları
        self.term_map = {
            "Yield": "Tahvil Faizi",
            "Federal Reserve": "FED",
            "Interest Rate": "Faiz Oranı",
            "Inflation": "Enflasyon",
            "Output": "Üretim",
            "Crude": "Ham",
            "Oil": "Petrol",
            "Stocks": "Hisseler",
            "Market": "Piyasa",
            "Markets": "Piyasalar",
            "Gains": "Yükseliş",
            "Losses": "Düşüş",
            "Surge": "Sert Yükseliş",
            "Plunge": "Sert Düşüş",
            "Jump": "Sıçrayış",
            "Drop": "Düşüş",
            "Fall": "Düşüş",
            "Rise": "Artış",
            "Extend": "Sürdürdü",
            "Extended": "Sürdürdü",
            "Streak": "Seri",
            "Uncertainty": "Belirsizlik",
            "Volatility": "Oynaklık",
            "Growth": "Büyüme",
            "Fear": "Korku",
            "Greed": "Açgözlülük",
            "Sentiment": "Duyarlılık",
            "Indices": "Endeksler",
            "Shares": "Hisseler",
            "Treasury": "Hazine",
            "Bonds": "Tahviller",
            "Security": "Güvenliği",
            "Reshaping": "Yeniden Şekillendiriyor",
            "Case": "Durum",
            "Investment": "Yatırım",
            "Assess": "Değerlendiriyor",
            "Amid": "Ortasında",
            "Ongoing": "Devam Eden",
            "Adjustments": "Düzenlemeler",
            "Wholesale": "Toptan",
            "Cools": "Soğuyor",
            "Tumbles": "Düşüyor",
            "Soars": "Yükseliyor",
            "Rallies": "Yükseliyor",
            "Cracks": "Çatlaklar",
            "Demanded": "Talep Etti",
            "Complete": "Tam",
            "Reopening": "Yeniden Açılmasını",
            "Strait of Hormuz": "Hürmüz Boğazı",
            "Gold": "Altın",
            "Silver": "Gümüş",
            "Copper": "Bakır",
            "Natural Gas": "Doğalgaz",
            "U.S.": "ABD",
            "Global": "Küresel",
            "Northeast": "Kuzeydoğu",
            "Williams": "Williams",
            "Gas": "Gaz",
            "Expansion": "Genişleme",
        }

        # Düğümlere (trigger_id) göre dinamik isim çevirileri
        self.node_names = {
            "fed_rate": "FED Faiz Oranı",
            "brent_oil": "Brent Petrol",
            "usd_try": "USD/TRY Kuru",
            "vix": "VIX Korku Endeksi",
            "gold": "Altın (Ons)",
            "silver": "Gümüş (Ons)",
            "natural_gas": "Doğalgaz",
            "us_10y_yield": "ABD 10Y Tahvil Faizi",
            "tr_cpi": "Türkiye Enflasyon (TÜFE)",
            "risk_appetite": "Küresel Risk İştahı",
            "foreign_equity_flow": "Yabancı Hisse Akışı",
            "bist100_index": "BIST100 Endeks",
        }

    def translate_headline(self, text: str) -> str:
        """
        Kural tabanlı finansal terim çevirisi.
        Cümle yapısını bozmadan finansal terimleri Türkçeleştirir.
        """
        if not text:
            return ""

        # 1. Kelime bazlı terim değiştirme
        words = text.split()
        translated_words = []
        for word in words:
            # Temizleme (noktalama işaretleri)
            clean_word = re.sub(r'[^\w\s]', '', word)
            suffix = word.replace(clean_word, '')
            
            if clean_word in self.term_map:
                translated_words.append(self.term_map[clean_word] + suffix)
            elif clean_word.capitalize() in self.term_map:
                translated_words.append(self.term_map[clean_word.capitalize()] + suffix)
            else:
                translated_words.append(word)

        translated_text = " ".join(translated_words)

        # 2. Kalıplaşmış tamlamalar için post-processing noktası.
        
        return translated_text

    def translate_node(self, node_id: str) -> str:
        """Düğüm ID'sini insan dostu Türkçe isme çevirir."""
        return self.node_names.get(node_id.lower(), node_id.replace("_", " ").title())

    def translate_magnitude(self, m: str) -> str:
        mapping = {"low": "Düşük", "medium": "Orta", "high": "Yüksek", "extreme": "Çok Yüksek"}
        return mapping.get(m.lower(), m)

    def translate_direction(self, d: str) -> str:
        mapping = {"up": "Yükseliş", "down": "Düşüş"}
        return mapping.get(d.lower(), d)

# Singleton
financial_translator = FinancialTranslator()
