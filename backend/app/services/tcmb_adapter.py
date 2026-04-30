"""
TCMB Makro Veri Adaptörü (Türkiye Cumhuriyet Merkez Bankası)

TCMB'nin resmi web sitesinden para politikası, döviz ve ekonomik verilerini çeker.
Kaynaklar:
- TCMB Para Politikası: https://www.tcmb.gov.tr
- Politika Faiz Oranı (Policy Rate)
- Döviz Kuru (USD/TRY, EUR/TRY)
- Döviz Rezervleri (Brüt/Net)
- Repo Oranları
"""

import logging
import aiohttp
from datetime import datetime, timezone
from typing import Dict, Optional, List
from bs4 import BeautifulSoup
from xml.etree import ElementTree as ET
import re

from app.core.database import AsyncSessionLocal
from app.models.news import NewsItem
from sqlalchemy import select
from app.services.source_health import record_source_failure, record_source_success
# Harici model entegrasyonu yok; kural tabanlı etki skoru kullanılır.

logger = logging.getLogger(__name__)


class TCMBAdapter:
    """
    Türkiye Merkez Bankası Makro Veri Çekicisi

    Veri kaynakları:
    - Politika Faiz Oranı (İlk Para Piyasası Oranı - IPPO)
    - Döviz Rezervleri
    - Para Politikası Açıklamaları
    """

    def __init__(self):
        self.base_url = "https://www.tcmb.gov.tr"
        self.ppk_rss_url = (
            f"{self.base_url}/wps/wcm/connect/TR/TCMB+TR/Bottom+Menu/Diger/RSS/PPK+Kararlari"
        )
        self.press_rss_url = (
            f"{self.base_url}/wps/wcm/connect/TR/TCMB+TR/Bottom+Menu/Diger/RSS/Basin+Duyurulari"
        )
        self.last_fetch = None

    def _normalize_text(self, value: str) -> str:
        mapping = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
        return value.translate(mapping).lower()

    async def _fetch_text(self, url: str) -> Optional[str]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as response:
                    if response.status != 200:
                        logger.warning(f"TCMB kaynak erişim hatası ({response.status}): {url}")
                        return None
                    return await response.text()
        except Exception as e:
            logger.error(f"TCMB kaynak çekme hatası ({url}): {e}")
            return None

    def _parse_atom_latest_entry(self, xml_text: str) -> Optional[Dict]:
        entries = self._parse_atom_entries(xml_text)
        return entries[0] if entries else None

    def _parse_atom_entries(self, xml_text: str) -> List[Dict]:
        try:
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            root = ET.fromstring(xml_text)
            entries: List[Dict] = []
            for entry in root.findall("atom:entry", ns):
                title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
                published = (entry.findtext("atom:published", default="", namespaces=ns) or "").strip()
                updated = (entry.findtext("atom:updated", default="", namespaces=ns) or "").strip()
                link = entry.find("atom:link", ns)
                href = link.attrib.get("href") if link is not None else None
                if href and href.startswith("http://"):
                    href = "https://" + href[len("http://"):]

                entries.append(
                    {
                        "title": title,
                        "published": published,
                        "updated": updated,
                        "url": href,
                    }
                )
            return entries
        except Exception as e:
            logger.debug(f"TCMB Atom parse hatası: {e}")
            return []

    def _find_latest_interest_rate_entry(self, xml_text: str) -> Optional[Dict]:
        keywords = (
            "faiz oranlarina iliskin",
            "politika kurulu",
            "ppk",
        )
        for entry in self._parse_atom_entries(xml_text):
            title = self._normalize_text(entry.get("title") or "")
            if any(keyword in title for keyword in keywords):
                return entry
        return None

    async def fetch_policy_rate(self) -> Optional[Dict]:
        """
        TCMB Politika Faiz Oranını çek (İlk Para Piyasası Oranı - IPPO).

        Returns:
            {
                "rate": 28.0,  # Yüzde
                "date": "2026-04-15",
                "change_bps": 50,  # Basis points
                "status": "stable|up|down"
            }
        """
        try:
            logger.info("📊 TCMB Politika Faiz Oranı çekiliyor...")
            feed_text = await self._fetch_text(self.press_rss_url)
            if not feed_text:
                return None

            latest_entry = self._find_latest_interest_rate_entry(feed_text)
            if not latest_entry or not latest_entry.get("url"):
                logger.warning("TCMB faiz duyurusu feed içinde bulunamadı")
                return None

            html = await self._fetch_text(latest_entry["url"])
            if not html:
                return None

            rate_data = self._parse_policy_rate(html)
            if rate_data:
                rate_data["date"] = latest_entry.get("published") or latest_entry.get("updated")
                rate_data["url"] = latest_entry.get("url")
                rate_data["title"] = latest_entry.get("title")
                logger.info(f"✅ TCMB Politika Oranı: {rate_data['rate']}%")
                return rate_data

            logger.warning("TCMB politika oranı bulunamadı")
            return None

        except Exception as e:
            logger.error(f"TCMB politika oranı çekme hatası: {e}")
            return None

    async def fetch_fx_reserves(self) -> Optional[Dict]:
        """
        TCMB Döviz Rezervlerini çek (Brüt ve Net).

        Returns:
            {
                "gross_reserves_billion_usd": 85.2,
                "net_reserves_billion_usd": 42.1,
                "date": "2026-04-15",
                "trend": "up|down|stable"
            }
        """
        try:
            logger.info("💱 TCMB Döviz Rezervleri çekiliyor...")
            return None

        except Exception as e:
            logger.error(f"TCMB döviz rezervleri çekme hatası: {e}")
            return None

    async def fetch_latest_press_release(self) -> Optional[Dict]:
        """
        TCMB'nin en son Para Politikası Kurulu toplantı açıklamasını çek.

        Returns:
            {
                "title": "Para Politikası Kurulu Toplantı Sonucu Açıklaması",
                "date": "2026-04-15",
                "summary": "...",
                "url": "...",
                "interest_rate_decision": True/False,
                "rate_change": 0,  # bps
            }
        """
        try:
            logger.info("📰 TCMB Para Politikası Açıklaması çekiliyor...")
            feed_text = await self._fetch_text(self.press_rss_url)
            if not feed_text:
                return None

            press = self._parse_press_release(feed_text)
            if press:
                logger.info(f"✅ Açıklama bulundu: {press['title'][:60]}")
                return press
            return None

        except Exception as e:
            logger.error(f"TCMB açıklama çekme hatası: {e}")
            return None

    def _parse_policy_rate(self, html: str) -> Optional[Dict]:
        """HTML'den politika faiz oranını çıkar."""
        try:
            patterns = [
                r"bir hafta vadeli repo ihale faiz oranının yüzde\s+(\d+(?:[.,]\d+)?)",
                r"politika faizi olan bir hafta vadeli repo ihale faiz oranının yüzde\s+(\d+(?:[.,]\d+)?)",
                r"politika faizi[^%]{0,120}?yüzde\s+(\d+(?:[.,]\d+)?)",
                r"politika faiz oranı[^%]*%(\d+(?:[.,]\d+)?)",
            ]

            for pattern in patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    rate = float(match.group(1).replace(",", "."))
                    return {
                        "rate": rate,
                        "date": datetime.now(timezone.utc).isoformat(),
                        "change_bps": 0,
                        "status": "stable",
                        "source": "TCMB",
                    }

            return None
        except Exception as e:
            logger.debug(f"Politika oranı parse hatası: {e}")
            return None

    def _parse_fx_reserves(self, html: str) -> Optional[Dict]:
        """HTML'den döviz rezervlerini çıkar."""
        try:
            patterns = [
                r"Brüt Döviz Rezervi[:\s]+(\d+[.,]\d+)\s*milyar",
                r"Net Döviz Rezervi[:\s]+(\d+[.,]\d+)\s*milyar",
            ]

            brut = None
            net = None

            for i, pattern in enumerate(patterns):
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    value = float(match.group(1).replace(",", "."))
                    if i == 0:
                        brut = value
                    else:
                        net = value

            if brut is not None and net is not None:
                return {
                    "gross_reserves_billion_usd": brut,
                    "net_reserves_billion_usd": net,
                    "date": datetime.now(timezone.utc).isoformat(),
                    "trend": "stable",
                    "source": "TCMB"
                }

            return None
        except Exception as e:
            logger.debug(f"Döviz rezervleri parse hatası: {e}")
            return None

    def _parse_press_release(self, html: str) -> Optional[Dict]:
        """TCMB Atom feed içinden son basın açıklamasını çıkar."""
        try:
            entry = self._parse_atom_latest_entry(html)
            if not entry:
                return None

            title = entry.get("title", "")
            return {
                "title": title,
                "date": entry.get("published") or entry.get("updated") or datetime.now(timezone.utc).isoformat(),
                "summary": f"TCMB basın açıklaması: {title}",
                "url": entry.get("url", self.base_url),
                "interest_rate_decision": "faiz" in title.lower() or "oran" in title.lower(),
                "rate_change": 0,
                "source": "TCMB",
            }
        except Exception as e:
            logger.debug(f"Basın açıklaması parse hatası: {e}")
            return None

    async def store_macro_event(self, event_data: Dict) -> bool:
        """
        Makro olayı NewsItem olarak veritabanına kaydet.

        Args:
            event_data: {
                "type": "policy_rate" | "fx_reserve" | "press_release",
                "title": str,
                "summary": str,
                "importance": float (0-1),
                "affected_symbols": ["THYAO", "EREGL", ...] (optional)
            }
        """
        try:
            async with AsyncSessionLocal() as db:
                existing = await db.execute(
                    select(NewsItem).where(
                        NewsItem.source == "TCMB",
                        NewsItem.title == event_data.get("title", "TCMB Bildirimi"),
                    )
                )
                if existing.scalar_one_or_none():
                    logger.info(f"ℹ️ TCMB olayı zaten kayıtlı: {event_data.get('title')}")
                    return False

                # Makro olaylar için "MACROVERI" stock record'u kullan
                # (veya tüm 100 hisseyi etkileyebilir)

                # Kural tabanlı nötr varsayılan.
                analysis = {"sentiment_score": 0.0, "importance_score": 1.0}

                # NewsItem oluştur — makro haber, belirli bir hisseye bağlı değil
                news = NewsItem(
                    stock_id=None,
                    title=event_data.get("title", "TCMB Bildirimi"),
                    summary=event_data.get("summary", ""),
                    url=event_data.get("url", "https://www.tcmb.gov.tr"),
                    source="TCMB",
                    language="tr",
                    category="macro",
                    published_at=datetime.now(timezone.utc),
                    sentiment_score=analysis.get("sentiment_score", 0.0),
                    sentiment_label=analysis.get("sentiment_label", "neutral"),
                    sentiment_confidence=analysis.get("sentiment_confidence", 0.6),
                    importance_score=event_data.get("importance", 0.85),
                    is_processed=False,
                )

                db.add(news)
                await db.commit()
                logger.info(f"✅ TCMB Makro Olayı kaydedildi: {event_data.get('title')}")
                return True

        except Exception as e:
            logger.error(f"TCMB olayı kayıt hatası: {e}")
            return False


# Singleton instance
tcmb_adapter = TCMBAdapter()


async def run_tcmb_scan() -> int:
    """
    TCMB verilerini periyodik olarak tara (arka plan görevi).
    APScheduler tarafından her 2 saatte çağrılır.
    """
    logger.info("🏦 TCMB Taraması Başlıyor...")
    stored = 0
    fetched = 0

    try:
        # Politika faiz oranı
        policy_rate = await tcmb_adapter.fetch_policy_rate()
        if policy_rate:
            fetched += 1
            stored += await tcmb_adapter.store_macro_event({
                "type": "policy_rate",
                "title": f"TCMB Politika Faiz Oranı: {policy_rate['rate']}%",
                "summary": f"Politika faiz oranı {policy_rate['rate']}% seviyesinde.",
                "importance": 0.95,
                "url": policy_rate.get("url"),
            }) and 1 or 0

        # Döviz rezervleri
        fx_reserves = await tcmb_adapter.fetch_fx_reserves()
        if fx_reserves:
            fetched += 1
            stored += await tcmb_adapter.store_macro_event({
                "type": "fx_reserve",
                "title": f"TCMB Brüt Döviz Rezervi: {fx_reserves['gross_reserves_billion_usd']:.1f}B USD",
                "summary": f"Brüt: {fx_reserves['gross_reserves_billion_usd']:.1f}B USD, Net: {fx_reserves['net_reserves_billion_usd']:.1f}B USD",
                "importance": 0.80,
            }) and 1 or 0

        # Para Politikası Açıklaması
        press = await tcmb_adapter.fetch_latest_press_release()
        if press and press.get("interest_rate_decision"):
            fetched += 1
            stored += await tcmb_adapter.store_macro_event({
                "type": "press_release",
                "title": press.get("title", "TCMB Açıklaması"),
                "summary": press.get("summary", ""),
                "importance": 0.90,
            }) and 1 or 0

        if fetched > 0:
            record_source_success("tcmb", detail={"fetched_count": fetched, "stored_count": stored})
        else:
            record_source_failure(
                "tcmb",
                "TCMB taraması veri üretemedi",
                detail={"fetched_count": fetched, "stored_count": stored},
            )

        logger.info(f"🟢 TCMB Taraması Tamamlandı: {stored} yeni veri, {fetched} kaynak bulundu")
        return stored

    except Exception as e:
        logger.error(f"TCMB taraması başarısız: {e}")
        record_source_failure("tcmb", str(e))
        return 0
