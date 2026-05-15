import logging
import yfinance as yf
from typing import List, Dict, Optional
from datetime import datetime, timezone
import random
import time
import concurrent.futures
from app.services.translator import financial_translator
from app.core.database import AsyncSessionLocal
from sqlalchemy import select
from app.models.stock import Stock

logger = logging.getLogger(__name__)

# ── Türkçe NLP: kural tabanlı duygu sınıflandırıcı ─────────────────────────
TURKISH_POSITIVE_KEYWORDS = [
    "artis", "buyume", "kar", "rekor", "guclu", "olumlu", "yukselis",
    "kazanc", "basari", "ihracat artisi", "temettu", "yatirim", "anlesma",
    "sozlesme", "ihale", "buyuyor", "artti", "yukseldi", "geri alim",
    "not artirimi", "gorunum pozitif", "surplus", "beat", "strong", "growth",
    "upgrade", "rally", "gain", "recovery",
]
TURKISH_NEGATIVE_KEYWORDS = [
    "dusus", "zarar", "kayip", "risk", "zayif", "olumsuz", "kriz",
    "baski", "gerileme", "endise", "iptal", "ceza", "dava", "sorusturma",
    "geriledi", "azaldi", "konkordato", "not indirimi", "gorunum negatif",
    "miss", "weak", "downgrade", "loss", "drop", "fall", "cut", "crash",
    "tumble", "decline", "probe", "lawsuit",
]


def classify_turkish_sentiment(text: str) -> float:
    """
    Türkce ve Ingilizce karma anahtar kelimelerle haber basligini skora cevir.
    Donus: -1.0 ile +1.0 arasi float (MacroNewsCollector._score_headline ile ayni aralik).
    """
    # Türkce karakterleri normalize et
    mapping = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    text_norm = text.translate(mapping).lower()

    pos = sum(1 for kw in TURKISH_POSITIVE_KEYWORDS if kw in text_norm)
    neg = sum(1 for kw in TURKISH_NEGATIVE_KEYWORDS if kw in text_norm)
    raw = (pos * 0.22) - (neg * 0.22)
    return max(-1.0, min(1.0, raw))


class MacroNewsCollector:
    """
    BIST100 haber ve olay ağı.
    Kaynaklar ülkeye göre değil, BIST üzerindeki tahmini etkilerine göre sıralanır.
    Hız sınırlarını (Rate-limit) aşmak için endeks bazlı ve rotasyonel tarama yapar.
    """

    def __init__(self):
        # Temel Küresel Makro Semboller
        self.macro_symbols = {
            "BZ=F": "brent_oil",
            "GC=F": "gold",
            "TRY=X": "usd_try",
            "^VIX": "vix",
            "SI=F": "silver",
            "NG=F": "natural_gas",
            "^TNX": "us_10y_yield",
        }
        
        # Her döngüde taranacak BIST Lokomotifleri (Öncelikli — Nisan 2026 güncel)
        self.priority_bist = [
            "XU100.IS",  # BIST100 Endeks (tüm piyasayı yansıtır)
            "THYAO.IS",  # Türk Hava Yolları — en büyük halka açık şirket
            "GARAN.IS",  # Garanti Bankası
            "EREGL.IS",  # Ereğli Demir Çelik
            "KCHOL.IS",  # Koç Holding
            "TUPRS.IS",  # Tüpraş
            "SISE.IS",   # Şişe Cam
            "ASELS.IS",  # Aselsan
            "BIMAS.IS",  # BİM
            "ISCTR.IS",  # İş Bankası
        ]
        
        # Rotasyon takibi için hisse listesi
        self._rotation_index = 0
        self._all_bist_symbols = []

        self.surge_keywords = [
            "surge", "jump", "soar", "spike", "skyrocket", "hike", "rally", "gain",
            "ustunde", "yukselis", "artti", "rekor", "yukseldi",
            "üstünde", "yükseliş", "artış",
        ]
        self.plunge_keywords = [
            "plunge", "crash", "tumble", "drop", "fall", "slide", "cut", "decline",
            "altinda", "dusus", "geriledi", "azaldi",
            "altında", "düşüş", "gerileme",
        ]
        self.extreme_keywords = [
            "record", "massive", "extreme", "historic", "shock", "panic", "collapse",
            "rekor", "sok", "cokus", "tarihi", "asiri",
            "şok", "çöküş", "tarihi",
        ]

    async def _update_bist100_list(self):
        """DB'den tüm listeyi çeker."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Stock.symbol).where(Stock.is_bist100))
            symbols = [f"{s[0]}.IS" for s in result.all() if f"{s[0]}.IS" not in self.priority_bist]
            self._all_bist_symbols = symbols

    def _fetch_single_ticker_news(self, symbol: str, trigger_id: str) -> List[Dict]:
        """Tek bir sembol haberini güvenli çek (Rate-limit korumalı)."""
        try:
            # Jitter: API'ları boğmamak için ufak rastgele beklemeler
            time.sleep(random.uniform(0.1, 0.5))
            
            ticker = yf.Ticker(symbol)
            news = ticker.news
            if not news:
                return []

            latest_news = news[0]
            content = latest_news.get('content', {})
            title = content.get('title', '')
            link = content.get('canonicalUrl', {}).get('url', '')
            publisher = content.get('provider', {}).get('displayName', 'Kaynak')
            pub_date_str = content.get('pubDate') or content.get('displayTime')

            if not title:
                return []

            # V1.3.1: Tazelik Kontrolü (Last 48 Hours)
            if pub_date_str:
                try:
                    # '2026-03-14T01:00:49Z' formatını parse et
                    pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                    diff = datetime.now(pub_date.tzinfo) - pub_date
                    if diff.days >= 2:
                        logger.debug(f"🗄️ Eski haber atlandı ({symbol}): {pub_date_str}")
                        return []
                except Exception:
                    # Parse hatası durumunda bugünkü tarih varsay
                    pub_date = datetime.now(timezone.utc)
            else:
                pub_date = datetime.now(timezone.utc)

            compound = self._score_headline(title)
            
            # Alakasız haberleri filtrele
            if abs(compound) < 0.1 and not any(w in title.lower() for w in self.surge_keywords + self.plunge_keywords):
                return []

            direction = self._determine_direction(title, compound, trigger_id)
            magnitude = self._determine_magnitude(title, compound)
            
            return [{
                "trigger_id": trigger_id,
                "direction": direction,
                "magnitude": magnitude,
                "headline": financial_translator.translate_headline(title),
                "original_headline": title,
                "source_url": link,
                "publisher": financial_translator.translate_headline(publisher),
                "sentiment_score": compound,
                "timestamp": pub_date.isoformat()
            }]
        except Exception as e:
            if "Too Many Requests" in str(e):
                logger.warning(f"⚠️ Rate limited on {symbol}. Waiting...")
            return []

    def _score_headline(self, headline: str) -> float:
        return classify_turkish_sentiment(headline)

    def _determine_magnitude(self, headline: str, sentiment_compound: float) -> str:
        headline_lower = headline.lower()
        if any(w in headline_lower for w in self.extreme_keywords) or abs(sentiment_compound) > 0.7:
            return "extreme"
        if abs(sentiment_compound) > 0.4:
            return "high"
        if abs(sentiment_compound) > 0.2:
            return "medium"
        return "low"

    def _determine_direction(self, headline: str, sentiment_compound: float, trigger_id: str) -> str:
        headline_lower = headline.lower()
        up_score = sum(1 for w in self.surge_keywords if w in headline_lower)
        down_score = sum(1 for w in self.plunge_keywords if w in headline_lower)
        if up_score > down_score:
            return "up"
        if down_score > up_score:
            return "down"
        if trigger_id == "usd_try" and "lira" in headline_lower and sentiment_compound < 0:
            return "up"
        return "up" if sentiment_compound > 0 else "down"

    def _parse_timestamp(self, timestamp: Optional[str]) -> datetime:
        if not timestamp:
            return datetime.min

        try:
            return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except Exception:
            return datetime.min

    def _event_priority(self, event: Dict) -> tuple:
        publisher = (event.get("publisher") or "").lower()
        source_url = (event.get("source_url") or "").lower()
        is_kap = "kap" in publisher or "kap.org.tr" in source_url
        sentiment_strength = abs(float(event.get("sentiment_score", 0) or 0))
        recency = self._parse_timestamp(event.get("timestamp")).timestamp()

        return (
            0 if is_kap else 1,
            -sentiment_strength,
            -recency,
        )

    async def fetch_real_events(self) -> List[Dict]:
        """
        Tarama döngüsü:
        1. Küresel Makroları tara.
        2. BIST100 Endeks ve Lokomotifleri tara (Her zaman).
        3. Yan tahtalardan 12 tanesini rotasyonla tara (Böylece 10 dakikada tüm 100 hisse taranır).
        """
        logger.info("Stalize haber radarı başlatıldı...")
        
        if not self._all_bist_symbols:
            await self._update_bist100_list()

        # Bu döngüdeki hedefler
        current_targets = {}
        
        # A. Küresel Makro
        for s, tid in self.macro_symbols.items():
            current_targets[s] = tid
        
        # B. Öncelikli BIST (Lokomotifler + Endeks)
        for s in self.priority_bist:
            current_targets[s] = "bist100_index"
        
        # C. Yan Tahta Rotasyonu (12 hisse/döngü)
        rotation_batch = self._all_bist_symbols[self._rotation_index : self._rotation_index + 12]
        for s in rotation_batch:
            current_targets[s] = "bist100_index"
        
        # Index'i güncelle
        self._rotation_index = (self._rotation_index + 12) % len(self._all_bist_symbols)

        events = []
        # Rate-limit koruması için worker sayısı 4'e indirildi
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_symbol = {
                executor.submit(self._fetch_single_ticker_news, sym, tid): sym 
                for sym, tid in current_targets.items()
            }
            for future in concurrent.futures.as_completed(future_to_symbol):
                res = future.result()
                if res:
                    events.extend(res)

        # Impact-first: KAP ve yüksek etkili içerikleri ülke fark etmeksizin öne al
        events.sort(key=self._event_priority)
        
        logger.info(f"Tarama tamam: {len(events)} olay. (Sıradaki rotasyon: {self._rotation_index})")
        return events


# Singleton
macro_news_collector = MacroNewsCollector()
