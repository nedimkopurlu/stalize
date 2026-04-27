"""
KAP Parser Service — Kamuyu Aydınlatma Platformu (Official Announcements)

Şirketlerin KAP'a yaptığı bildirimleri parse eder.
Bu, "Şirketler ne yapıyor?" sorusunun EN GÜVENİLİR cevabıdır (TIER 1).

Kaynaklar:
- KAP RSS: https://www.kap.org.tr/tr/Sorgu/Sayfalar/rss/StockNewsObligated
- KAP XML API: https://www.kap.org.tr (veri tabanı sorguları)
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Union

import feedparser  # hard import — missing feedparser raises ModuleNotFoundError at module load
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.news import NewsItem
from app.models.stock import Stock
from app.services.source_health import record_source_failure, record_source_success
# Harici model entegrasyonu yok; kural tabanlı duygu skoru kullanılıyor.

logger = logging.getLogger(__name__)


class KAPParser:
    """
    KAP (Özel Durum Bildirimleri) Parser
    
    Özellikler:
    - RSS feed'i günlük RSS taraması
    - PDF/XML analiz (ileride)
    - Entity linking (hangi hisseler etkileniyor?)
    - Impact scoring (etki şiddeti?)
    """
    
    def __init__(self):
        self.rss_url = settings.KAP_RSS_URL
        self.scan_interval = settings.KAP_SCAN_INTERVAL_MIN
        self.max_age_hours = settings.KAP_MAX_AGE_HOURS

    def _normalize_text(self, value: str) -> str:
        mapping = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
        return value.translate(mapping).lower()
        
    async def fetch_latest_announcements(self) -> List[Dict]:
        """
        KAP RSS feed'inden en yeni bildirimleri çek.
        
        Returns:
            [
                {
                    "title": "XYZ Şirketi Temettü Dağıtımı",
                    "link": "https://www.kap.org.tr/...",
                    "published": "2026-04-15T10:30:00Z",
                    "symbol": "XYZ",
                    "event_type": "dividend",
                    "content_summary": "..."
                }
            ]
        """
        logger.info("🔴 KAP RSS feed taranıyor...")

        try:
            # RSS'i parse et
            feed = feedparser.parse(self.rss_url)
            announcements = []
            
            for entry in feed.entries[:50]:  # Son 50 haber
                try:
                    pub_date = self._parse_date(entry.get('published', ''))
                    
                    # Çok eski haberler atla
                    if pub_date and (datetime.now(pub_date.tzinfo) - pub_date) > timedelta(hours=self.max_age_hours):
                        continue
                    
                    # Hisse sembolünü çıkar
                    symbols = self._extract_symbols(entry.get('title', '') + ' ' + entry.get('summary', ''))
                    
                    for symbol in symbols:
                        announcement = {
                            "title": entry.get('title', 'No Title'),
                            "link": entry.get('link', ''),
                            "published": pub_date.isoformat() if pub_date else datetime.now().isoformat(),
                            "symbol": symbol,
                            "event_type": self._classify_event(entry.get('title', '')),
                            "content_summary": entry.get('summary', '')[:500],  # İlk 500 char
                            "source": "KAP",
                        }
                        announcements.append(announcement)
                
                except Exception as e:
                    logger.warning(f"KAP haber parse hatası: {e}")
                    continue
            
            logger.info(f"✅ {len(announcements)} KAP bildirimi bulundu")
            record_source_success(
                "kap",
                detail={"fetched_count": len(announcements), "rss_url": self.rss_url},
            )
            return announcements
            
        except Exception as e:
            logger.warning(f"KAP RSS geçici olarak erişilemiyor: {e}. Boş liste döndürülüyor; bir sonraki taramada tekrar deneyecek.")
            record_source_failure(
                "kap",
                str(e),
                detail={"rss_url": self.rss_url},
            )
            return []

    async def store_announcements(self, announcements: List[Dict]) -> int:
        """
        Bildirimleri veritabanına kaydet.
        
        Returns:
            Kaydedilen benzersiz bildiri sayısı
        """
        async with AsyncSessionLocal() as db:
            stored_count = 0
            
            for ann in announcements:
                try:
                    # Duplikasyon kontrol
                    result = await db.execute(
                        select(NewsItem).where(
                            (NewsItem.url == ann['link']) |
                            (NewsItem.title == ann['title'])
                        )
                    )
                    if result.scalar_one_or_none():
                        continue  # Zaten var, atla
                    
                    # Hisseyi bul
                    stock_result = await db.execute(
                        select(Stock).where(Stock.symbol == ann['symbol'].upper())
                    )
                    stock = stock_result.scalar_one_or_none()
                    
                    if not stock:
                        logger.warning(f"Hisse bulunamadı: {ann['symbol']}")
                        continue
                    
                    event_type = ann.get("event_type") or self._classify_event(ann["title"])
                    analysis = self._analyze_announcement(ann["title"], event_type)

                    news = NewsItem(
                        stock_id=stock.id,
                        title=ann["title"],
                        summary=ann["content_summary"],
                        url=ann["link"],
                        source="KAP",
                        language="tr",
                        category=event_type,
                        published_at=self._parse_date(ann["published"]) or datetime.now(timezone.utc),
                        sentiment_score=analysis["sentiment_score"],
                        sentiment_label=analysis["sentiment_label"],
                        sentiment_confidence=analysis["sentiment_confidence"],
                        importance_score=analysis["importance_score"],
                        is_processed=False,
                    )
                    db.add(news)
                    self._apply_stock_sentiment(stock, news.sentiment_score, news.importance_score)
                    stored_count += 1
                    
                except Exception as e:
                    logger.warning(f"Haber kaydı hatası ({ann['symbol']}): {e}")
                    continue
            
            try:
                await db.commit()
                logger.info(f"✅ {stored_count} KAP bildirimi veritabanına kaydedildi")
            except Exception as e:
                logger.error(f"Commit hatası: {e}")
                await db.rollback()
            
            return stored_count
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse RFC 2822 tarih formatını."""
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except Exception:
            try:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except Exception:
                return None
    
    def _extract_symbols(self, text: str) -> List[str]:
        """
        Metinden BIST100 sembollerini çıkar.
        
        Örned:
        "THYAO ve PEGASUS'un birleşmesi" → ["THYAO", "PEGASUS"]
        """
        symbols = []
        text_upper = text.upper()
        
        for symbol in settings.BIST100_SYMBOLS:
            if symbol in text_upper:
                symbols.append(symbol)
        
        return list(set(symbols))  # Duplikasyon kaldır
    
    def _classify_event(self, title: str) -> str:
        """
        Haber türünü sınıflandır.

        Dönüş: "dividend", "bonus_issue", "rights_issue", "buyback", "earnings",
        "investment", "tender", "contract", "credit_rating", "financing",
        "share_sale", "merger", "governance", "legal", "restructuring", "other"
        """
        title_lower = self._normalize_text(title)

        if any(w in title_lower for w in ["temettu", "kar payi", "kar dagitim", "nakit kar payi", "dividend"]):
            return "dividend"

        if any(w in title_lower for w in ["bedelsiz", "ic kaynaklardan sermaye artirimi"]):
            return "bonus_issue"

        if any(w in title_lower for w in ["bedelli", "ruchan", "sermaye artirimi", "capital increase"]):
            return "rights_issue"

        if any(w in title_lower for w in ["geri alim", "pay geri alim", "share buyback", "buyback"]):
            return "buyback"

        if any(w in title_lower for w in ["finansal sonuc", "donem sonucu", "bilanco", "earnings", "results"]):
            return "earnings"

        if any(w in title_lower for w in ["yatirim", "kapasite artis", "tesis", "fabrika", "yatirim tesvik", "investment"]):
            return "investment"

        if any(w in title_lower for w in ["ihale", "tender", "teklif"]):
            return "tender"

        if any(w in title_lower for w in ["yeni is iliskisi", "sozlesme", "siparis", "is iliskisi"]):
            return "contract"

        if any(w in title_lower for w in ["derecelendirme", "rating", "not gorunumu", "kredi notu"]):
            return "credit_rating"

        if any(w in title_lower for w in ["tahvil", "bono", "borclanma araci", "sendikasyon", "kredi sozlesmesi", "eurobond", "finansman"]):
            return "financing"

        if any(w in title_lower for w in ["pay satis", "ortak satis", "blok satis", "hisse satis"]):
            return "share_sale"

        if any(w in title_lower for w in ["birlesme", "devralma", "satin alma", "acquisition", "merger"]):
            return "merger"

        if any(w in title_lower for w in ["genel kurul", "yonetim kurulu", "board", "corporate governance"]):
            return "governance"

        if any(w in title_lower for w in ["dava", "ceza", "sorusturma", "legal", "suit", "investigation"]):
            return "legal"

        if any(w in title_lower for w in ["yeniden yapilandirma", "konkordato", "restructuring", "reorganization"]):
            return "restructuring"

        return "other"

    def _analyze_announcement(self, title: str, event_type: str) -> Dict[str, Union[float, str]]:
        """KAP başlığını kural tabanlı duygu ve önem skoruna çevir."""
        neutral = {
            "sentiment_score": 0.0,
            "sentiment_label": "neutral",
            "sentiment_confidence": 0.65,
            "importance_score": 0.75,
        }

        scoring_map = {
            "dividend": {"sentiment_score": 0.55, "sentiment_label": "positive", "sentiment_confidence": 0.82, "importance_score": 0.88},
            "bonus_issue": {"sentiment_score": 0.42, "sentiment_label": "positive", "sentiment_confidence": 0.79, "importance_score": 0.9},
            "rights_issue": {"sentiment_score": -0.34, "sentiment_label": "negative", "sentiment_confidence": 0.8, "importance_score": 0.93},
            "buyback": {"sentiment_score": 0.6, "sentiment_label": "positive", "sentiment_confidence": 0.84, "importance_score": 0.86},
            "earnings": {"sentiment_score": 0.0, "sentiment_label": "neutral", "sentiment_confidence": 0.7, "importance_score": 0.9},
            "investment": {"sentiment_score": 0.35, "sentiment_label": "positive", "sentiment_confidence": 0.76, "importance_score": 0.83},
            "tender": {"sentiment_score": 0.48, "sentiment_label": "positive", "sentiment_confidence": 0.78, "importance_score": 0.88},
            "contract": {"sentiment_score": 0.5, "sentiment_label": "positive", "sentiment_confidence": 0.8, "importance_score": 0.84},
            "credit_rating": {"sentiment_score": 0.1, "sentiment_label": "neutral", "sentiment_confidence": 0.73, "importance_score": 0.78},
            "financing": {"sentiment_score": -0.05, "sentiment_label": "neutral", "sentiment_confidence": 0.72, "importance_score": 0.82},
            "share_sale": {"sentiment_score": -0.45, "sentiment_label": "negative", "sentiment_confidence": 0.82, "importance_score": 0.87},
            "merger": {"sentiment_score": 0.2, "sentiment_label": "neutral", "sentiment_confidence": 0.74, "importance_score": 0.9},
            "governance": {"sentiment_score": 0.05, "sentiment_label": "neutral", "sentiment_confidence": 0.66, "importance_score": 0.72},
            "legal": {"sentiment_score": -0.65, "sentiment_label": "negative", "sentiment_confidence": 0.86, "importance_score": 0.94},
            "restructuring": {"sentiment_score": -0.3, "sentiment_label": "negative", "sentiment_confidence": 0.78, "importance_score": 0.88},
            "other": neutral,
        }

        analysis = dict(scoring_map.get(event_type, neutral))
        title_lower = self._normalize_text(title)

        positive_boosters = [
            "rekor",
            "guclu",
            "temettu",
            "sozlesme",
            "yeni is iliskisi",
            "ihale kazan",
            "ihale sonucu",
            "yatirim tesvik",
            "geri alim",
            "not artir",
            "gorunum pozitif",
            "karlilikta artis",
            "karini artirdi",
        ]
        negative_boosters = [
            "zarar",
            "iptal",
            "ceza",
            "dava",
            "sorusturma",
            "konkordato",
            "not indir",
            "gorunum negatif",
            "pay satis",
            "sermaye artirimi basvurusu",
            "bedelli",
            "sozlesme feshi",
        ]

        if any(w in title_lower for w in positive_boosters):
            analysis["sentiment_score"] = min(1.0, float(analysis["sentiment_score"]) + 0.15)
            analysis["importance_score"] = min(1.0, float(analysis["importance_score"]) + 0.05)

        if any(w in title_lower for w in negative_boosters):
            analysis["sentiment_score"] = max(-1.0, float(analysis["sentiment_score"]) - 0.2)
            analysis["importance_score"] = min(1.0, float(analysis["importance_score"]) + 0.06)

        score = float(analysis["sentiment_score"])
        if score >= 0.2:
            analysis["sentiment_label"] = "positive"
        elif score <= -0.2:
            analysis["sentiment_label"] = "negative"
        else:
            analysis["sentiment_label"] = "neutral"

        thesis_profile = self._build_thesis_profile(event_type, title)
        analysis["thesis_horizon"] = thesis_profile["thesis_horizon"]
        analysis["thesis_weight"] = thesis_profile["thesis_weight"]
        analysis["thesis_reason"] = thesis_profile["thesis_reason"]

        return analysis

    def _build_thesis_profile(self, event_type: str, title: str) -> Dict[str, Union[float, str]]:
        title_lower = self._normalize_text(title)
        medium_term_events = {"dividend", "bonus_issue", "rights_issue", "earnings", "investment", "merger", "restructuring", "credit_rating", "financing"}
        short_term_events = {"buyback", "contract", "tender", "governance"}
        negative_long_tail = {"legal", "share_sale"}

        if event_type in medium_term_events:
            return {
                "thesis_horizon": "medium_term",
                "thesis_weight": 0.9,
                "thesis_reason": "Sirket tezi ve orta vade fiyatlama uzerinde dogrudan etkili kurumsal olay.",
            }
        if event_type in negative_long_tail:
            return {
                "thesis_horizon": "medium_term",
                "thesis_weight": 0.92,
                "thesis_reason": "Sermaye yapisi veya hukuki risk nedeniyle orta vade tezini bozabilir.",
            }
        if event_type in short_term_events:
            return {
                "thesis_horizon": "short_term",
                "thesis_weight": 0.68,
                "thesis_reason": "Kisa vadeli fiyatlama yaratabilir ancak kalici tez etkisi sinirli.",
            }
        if "yatirim" in title_lower or "finansal sonuc" in title_lower:
            return {
                "thesis_horizon": "medium_term",
                "thesis_weight": 0.86,
                "thesis_reason": "Baslik orta vade beklentiyi degistirebilecek unsur tasiyor.",
            }
        return {
            "thesis_horizon": "short_term",
            "thesis_weight": 0.6,
            "thesis_reason": "Baslik izlenmeli ancak tek basina tez degistirici guc sinirli.",
        }

    def _apply_stock_sentiment(self, stock: Stock, raw_sentiment: Optional[float], importance_score: Optional[float]) -> None:
        """KAP haberini hisse sentiment skoruna yansıt."""
        sentiment_score = raw_sentiment if raw_sentiment is not None else 0.0
        normalized = (sentiment_score + 1.0) / 2.0 * 100.0
        importance = importance_score if importance_score is not None else 0.6
        current_score = stock.sentiment_score if stock.sentiment_score is not None else 50.0
        blend_ratio = min(0.85, max(0.25, importance))
        stock.sentiment_score = (normalized * blend_ratio) + (current_score * (1.0 - blend_ratio))
        stock.last_data_update = datetime.now(timezone.utc)

    async def get_recent_feed(self, limit: int = 20) -> List[Dict]:
        """Son KAP bildirimlerini terminal akışı formatında döndür."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(NewsItem, Stock.symbol)
                .join(Stock, NewsItem.stock_id == Stock.id)
                .where(NewsItem.source == "KAP")
                .order_by(NewsItem.published_at.desc())
                .limit(limit)
            )
            rows = result.all()

        feed_items: List[Dict] = []
        for news, symbol in rows:
            feed_items.append({
                "trigger_id": symbol.lower(),
                "direction": "up" if (news.sentiment_score or 0) >= 0 else "down",
                "magnitude": "high" if (news.importance_score or 0) >= 0.9 else "medium",
                "headline": news.title,
                "original_headline": news.title,
                "source_url": news.url,
                "publisher": news.source,
                "sentiment_score": news.sentiment_score or 0.0,
                "timestamp": news.published_at.isoformat() if news.published_at else datetime.now(timezone.utc).isoformat(),
                "category": news.category,
                "importance_score": news.importance_score,
                "symbol": symbol,
                "thesis_horizon": self._build_thesis_profile(news.category or "other", news.title)["thesis_horizon"],
                "thesis_weight": self._build_thesis_profile(news.category or "other", news.title)["thesis_weight"],
            })

        return feed_items

    async def get_recent_scenarios(self, limit: int = 10) -> List[Dict]:
        """KAP bildirimlerinden doğrudan şirket etkisi senaryoları üret."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(NewsItem, Stock)
                .join(Stock, NewsItem.stock_id == Stock.id)
                .where(NewsItem.source == "KAP")
                .order_by(NewsItem.published_at.desc())
                .limit(limit)
            )
            rows = result.all()

        scenarios: List[Dict] = []
        for news, stock in rows:
            raw_sentiment = news.sentiment_score if news.sentiment_score is not None else 0.0
            confidence = news.sentiment_confidence if news.sentiment_confidence is not None else 0.7
            importance = news.importance_score if news.importance_score is not None else 0.65
            impact_score = max(-100.0, min(100.0, raw_sentiment * importance * 100.0))
            impact_pct = max(-15.0, min(15.0, impact_score * 0.08))
            direction = "positive" if impact_score >= 0 else "negative"

            scenarios.append({
                "scenario": {
                    "trigger": f"{stock.symbol} KAP Bildirimi",
                    "trigger_id": f"kap_{stock.symbol.lower()}",
                    "direction": "up" if impact_score >= 0 else "down",
                    "magnitude": "high" if importance >= 0.85 else "medium",
                    "category": "company_disclosure",
                    "source_news_headline": news.title,
                    "source_url": news.url,
                    "publisher": news.source,
                    "computed_at": news.published_at.isoformat() if news.published_at else datetime.now(timezone.utc).isoformat(),
                    "thesis_horizon": self._build_thesis_profile(news.category or "other", news.title)["thesis_horizon"],
                    "thesis_weight": self._build_thesis_profile(news.category or "other", news.title)["thesis_weight"],
                },
                "impacts": [
                    {
                        "symbol": stock.symbol,
                        "name": stock.name,
                        "sector": stock.sector,
                        "current_price": stock.current_price,
                        "direction": direction,
                        "impact_score": round(impact_score, 2),
                        "impact_pct": round(impact_pct, 2),
                        "reasons": [news.title],
                        "confidence": round(confidence, 2),
                        "chain_depth": 1,
                    }
                ],
                "chain_analysis": [],
                "summary": {
                    "headline": news.title,
                    "total_stocks_affected": 1,
                    "positive_stocks": 1 if impact_score >= 0 else 0,
                    "negative_stocks": 0 if impact_score >= 0 else 1,
                    "top_winners": [{"symbol": stock.symbol, "score": round(impact_score, 1)}] if impact_score >= 0 else [],
                    "top_losers": [{"symbol": stock.symbol, "score": round(impact_score, 1)}] if impact_score < 0 else [],
                },
                "computed_at": news.published_at.isoformat() if news.published_at else datetime.now(timezone.utc).isoformat(),
            })

        return scenarios


# Singleton instance
kap_parser = KAPParser()


async def run_kap_scan() -> int:
    """
    Düzenli KAP taraması (arka plan görevi).
    APScheduler tarafından her 5 dakikada çağrılır.
    """
    logger.info("🔴 KAP Tarayıcısı Başlıyor...")
    
    try:
        # Yeni bildirimleri çek
        announcements = await kap_parser.fetch_latest_announcements()
        
        # Veritabanına kaydet
        stored = await kap_parser.store_announcements(announcements)
        record_source_success(
            "kap",
            detail={"fetched_count": len(announcements), "stored_count": stored},
        )
        
        logger.info(f"🟢 KAP Taraması Tamamlandı: {stored} yeni bildiri")
        return stored
        
    except Exception as e:
        logger.error(f"KAP taraması başarısız: {e}")
        record_source_failure("kap", str(e))
        return 0
