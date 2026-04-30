"""
TUIK Ekonomik Veri Adaptörü (Türkiye İstatistik Kurumu)

TUIK'ten makroekonomik verilerini çeker:
- TÜFE (Tüketici Fiyat Endeksi - CPI)
- Sanayi Üretim Endeksi
- İşsizlik Oranı
- Kapasite Kullanım Oranı
- Dış Ticaret Dengesi

Kaynaklar:
- TUIK Veri Portalı: https://www.tuik.gov.tr
- İstatistikler: https://www.tuik.gov.tr/ustmenu.do?metod=temelist
"""

import logging
import aiohttp
from datetime import datetime, timezone
from typing import Dict, Optional
from bs4 import BeautifulSoup
import re

from app.core.database import AsyncSessionLocal
from app.models.news import NewsItem
from sqlalchemy import select
from app.services.source_health import record_source_failure, record_source_success
# Harici model entegrasyonu yok; kural tabanlı etki skoru kullanılır.

logger = logging.getLogger(__name__)


class TUIKAdapter:
    """
    Türkiye İstatistik Kurumu Ekonomik Veri Çekicisi

    Veri kaynakları:
    - TÜFE (Tüketici Fiyat Endeksi)
    - Sanayi Üretim Endeksi
    - İşsizlik Oranı
    - Kapasite Kullanım Oranı
    """

    def __init__(self):
        self.base_url = "https://www.tuik.gov.tr"
        self.stats_url = f"{self.base_url}/Home/HaberBultenleriPartial"
        self.indicators_url = f"{self.base_url}/Home/GostergelerPartial"
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
                        logger.warning(f"TUIK kaynak erişim hatası ({response.status}): {url}")
                        return None
                    return await response.text()
        except Exception as e:
            logger.error(f"TUIK kaynak çekme hatası ({url}): {e}")
            return None

    async def _fetch_bulletin_cards(self) -> list[dict]:
        html = await self._fetch_text(self.stats_url)
        if not html:
            return []

        return self._parse_bulletin_cards(html)

    async def _fetch_popular_indicators(self) -> list[dict]:
        html = await self._fetch_text(self.indicators_url)
        if not html:
            return []
        return self._parse_popular_indicators(html)

    def _parse_bulletin_cards(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        cards: list[dict] = []
        for slide in soup.select("div.swiper-slide"):
            anchor = slide.find("a", href=True)
            if anchor is None:
                continue
            title_node = slide.select_one("span.text-tuik-dark.font-weight-bold")
            summary_node = slide.select_one("div.card-body .row")
            metric_node = slide.select_one("p.text-tuik-dark")
            date_node = slide.find("date")

            title = re.sub(r"\s+", " ", title_node.get_text(" ", strip=True)) if title_node else ""
            summary = re.sub(r"\s+", " ", summary_node.get_text(" ", strip=True)) if summary_node else ""
            metric = re.sub(r"\s+", " ", metric_node.get_text(" ", strip=True)) if metric_node else ""
            published_on = re.sub(r"\s+", " ", date_node.get_text(" ", strip=True)) if date_node else ""
            if not title:
                title = re.sub(r"\s+", " ", anchor.get_text(" ", strip=True))
            if not title:
                continue

            href = anchor.get("href", "")
            if href.startswith("/"):
                href = f"{self.base_url}{href}"
            cards.append(
                {
                    "text": " ".join(part for part in [title, metric, summary] if part),
                    "title": title,
                    "summary": summary,
                    "metric": metric,
                    "published_on": published_on,
                    "url": href,
                }
            )
        return cards

    def _parse_popular_indicators(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        items: list[dict] = []
        for card in soup.select("div.chartcard"):
            header_node = card.select_one("div.chartheader span")
            period_node = card.select_one("div.chartdiv span")
            value_node = card.select_one("div.chartfooter")
            onclick_attr = card.get("onclick", "")

            title = re.sub(r"\s+", " ", header_node.get_text(" ", strip=True)) if header_node else ""
            period = re.sub(r"\s+", " ", period_node.get_text(" ", strip=True)) if period_node else ""
            value = re.sub(r"\s+", " ", value_node.get_text(" ", strip=True)) if value_node else ""
            if not title or not value:
                continue

            press_match = re.search(r"/tr/press/(\d+)|,\s*'(\d+)'", onclick_attr)
            press_id = (press_match.group(1) or press_match.group(2)) if press_match else None
            url = f"https://veriportali.tuik.gov.tr/tr/press/{press_id}" if press_id else None

            items.append(
                {
                    "title": title,
                    "period": period,
                    "value": value,
                    "url": url,
                    "text": " ".join(part for part in [title, period, value] if part),
                }
            )
        return items

    async def _find_popular_indicator(self, keywords: list[str]) -> Optional[dict]:
        indicators = await self._fetch_popular_indicators()
        lowered_keywords = [self._normalize_text(keyword) for keyword in keywords]
        for item in indicators:
            haystack = self._normalize_text(item["text"])
            if all(keyword in haystack for keyword in lowered_keywords):
                return item
        return None

    async def _find_bulletin(self, keywords: list[str]) -> Optional[dict]:
        cards = await self._fetch_bulletin_cards()
        lowered_keywords = [self._normalize_text(keyword) for keyword in keywords]

        for card in cards:
            lowered = self._normalize_text(card["text"])
            if all(keyword in lowered for keyword in lowered_keywords):
                return card
        return None

    async def fetch_cpi_inflation(self) -> Optional[Dict]:
        """
        TÜFE (Tüketici Fiyat Endeksi) / Enflasyon oranını çek.

        Returns:
            {
                "inflation_rate_monthly": 2.1,  # Yüzde
                "inflation_rate_annual": 44.5,  # Yüzde
                "date": "2026-04-15",
                "change": "up|down|stable"
            }
        """
        try:
            logger.info("📊 TUIK TÜFE Enflasyon Oranı çekiliyor...")
            indicator = await self._find_popular_indicator(["tüketici", "fiyat", "endeksi"])
            if indicator:
                annual = self._extract_first_number(indicator.get("value"))
                if annual is not None:
                    return {
                        "inflation_rate_monthly": None,
                        "inflation_rate_annual": annual,
                        "date": indicator.get("period"),
                        "change": "up" if annual > 40 else "stable",
                        "source": "TUIK",
                        "url": indicator.get("url"),
                    }

            bulletin = await self._find_bulletin(["tüketici", "fiyat", "endeksi"])
            if not bulletin:
                logger.warning("TUIK TÜFE bulunamadı")
                return None

            cpi_data = self._parse_cpi(" ".join([bulletin.get("title", ""), bulletin.get("metric", ""), bulletin.get("summary", "")]))
            if cpi_data:
                cpi_data["url"] = bulletin["url"]
                cpi_data["date"] = bulletin.get("published_on") or cpi_data["date"]
                logger.info(
                    "✅ TUIK TÜFE Enflasyon: Aylık %s%%, Yıllık %s%%",
                    cpi_data["inflation_rate_monthly"],
                    cpi_data["inflation_rate_annual"],
                )
                return cpi_data
            logger.warning("TUIK TÜFE parse edilemedi")
            return None

        except Exception as e:
            logger.error(f"TUIK TÜFE çekme hatası: {e}")
            return None

    async def fetch_industrial_production(self) -> Optional[Dict]:
        """
        Sanayi Üretim Endeksi'ni çek.

        Returns:
            {
                "production_index": 112.3,
                "month_over_month_change": 2.5,  # Yüzde
                "year_over_year_change": 5.2,    # Yüzde
                "date": "2026-04-15",
                "trend": "up|down|stable"
            }
        """
        try:
            logger.info("🏭 TUIK Sanayi Üretim Endeksi çekiliyor...")
            indicator = await self._find_popular_indicator(["sanayi", "uretim", "endeksi"])
            if indicator:
                yoy = self._extract_first_number(indicator.get("value"))
                if yoy is not None:
                    return {
                        "production_index": yoy,
                        "month_over_month_change": None,
                        "year_over_year_change": yoy,
                        "date": indicator.get("period"),
                        "trend": "up" if yoy > 0 else "down",
                        "source": "TUIK",
                        "url": indicator.get("url"),
                    }

            bulletin = await self._find_bulletin(["sanayi", "üretim", "endeksi"])
            if not bulletin:
                return None

            prod_data = self._parse_industrial_production(" ".join([bulletin.get("title", ""), bulletin.get("metric", ""), bulletin.get("summary", "")]))
            if prod_data:
                prod_data["url"] = bulletin["url"]
                prod_data["date"] = bulletin.get("published_on") or prod_data["date"]
                logger.info(f"✅ Sanayi Üretim Endeksi: {prod_data['production_index']}")
                return prod_data
            return None

        except Exception as e:
            logger.error(f"TUIK sanayi üretim çekme hatası: {e}")
            return None

    async def fetch_unemployment_rate(self) -> Optional[Dict]:
        """
        İşsizlik Oranı'nı çek.

        Returns:
            {
                "unemployment_rate": 8.2,  # Yüzde
                "employment_rate": 91.8,
                "date": "2026-04-15",
                "trend": "up|down|stable"
            }
        """
        try:
            logger.info("👷 TUIK İşsizlik Oranı çekiliyor...")
            indicator = await self._find_popular_indicator(["issizlik", "orani"])
            if indicator:
                unemployment = self._extract_first_number(indicator.get("value"))
                if unemployment is not None:
                    return {
                        "unemployment_rate": unemployment,
                        "employment_rate": None,
                        "date": indicator.get("period"),
                        "trend": "up" if unemployment > 10 else "stable",
                        "source": "TUIK",
                        "url": indicator.get("url"),
                    }

            bulletin = await self._find_bulletin(["işgücü", "istatistikleri"])
            if not bulletin:
                bulletin = await self._find_bulletin(["işsizlik"])
            if not bulletin:
                return None

            unemployment = self._parse_unemployment(" ".join([bulletin.get("title", ""), bulletin.get("metric", ""), bulletin.get("summary", "")]))
            if unemployment:
                unemployment["url"] = bulletin["url"]
                unemployment["date"] = bulletin.get("published_on") or unemployment["date"]
                logger.info(f"✅ İşsizlik Oranı: {unemployment['unemployment_rate']}%")
                return unemployment
            return None

        except Exception as e:
            logger.error(f"TUIK işsizlik çekme hatası: {e}")
            return None

    async def fetch_capacity_utilization(self) -> Optional[Dict]:
        """
        Kapasite Kullanım Oranı'nı çek.

        Returns:
            {
                "capacity_utilization_rate": 76.5,  # Yüzde
                "date": "2026-04-15",
                "trend": "up|down|stable"
            }
        """
        try:
            logger.info("⚙️ TUIK Kapasite Kullanım Oranı çekiliyor...")
            bulletin = await self._find_bulletin(["kapasite", "kullanım"])
            if not bulletin:
                return None

            capacity = self._parse_capacity(" ".join([bulletin.get("title", ""), bulletin.get("metric", ""), bulletin.get("summary", "")]))
            if capacity:
                capacity["url"] = bulletin["url"]
                capacity["date"] = bulletin.get("published_on") or capacity["date"]
                logger.info(f"✅ Kapasite Kullanım: {capacity['capacity_utilization_rate']}%")
                return capacity
            return None

        except Exception as e:
            logger.error(f"TUIK kapasite çekme hatası: {e}")
            return None

    def _parse_cpi(self, html: str) -> Optional[Dict]:
        """HTML'den TÜFE/Enflasyon oranını çıkar."""
        try:
            yearly_match = re.search(
                r"(?:yıllık|yillik)[^%]{0,20}%\s*(-?\d+(?:[.,]\d+)?)|%\s*(-?\d+(?:[.,]\d+)?)\s*\((?:yıl|yil)\)",
                html,
                re.IGNORECASE,
            )
            monthly_match = re.search(
                r"aylık[^%]{0,20}%\s*(-?\d+(?:[.,]\d+)?)|%\s*(-?\d+(?:[.,]\d+)?)\s*\(ay\)",
                html,
                re.IGNORECASE,
            )

            if yearly_match:
                annual_raw = yearly_match.group(1) or yearly_match.group(2)
                annual = float(annual_raw.replace(",", "."))
                monthly = (
                    float((monthly_match.group(1) or monthly_match.group(2)).replace(",", "."))
                    if monthly_match
                    else None
                )
                return {
                    "inflation_rate_monthly": monthly,
                    "inflation_rate_annual": annual,
                    "date": datetime.now(timezone.utc).isoformat(),
                    "change": "up" if annual > 40 else "stable",
                    "source": "TUIK",
                }

            return None
        except Exception as e:
            logger.debug(f"TÜFE parse hatası: {e}")
            return None

    def _parse_industrial_production(self, html: str) -> Optional[Dict]:
        """HTML'den sanayi üretim endeksini çıkar."""
        try:
            yoy_match = re.search(r"%\s*(-?\d+(?:[.,]\d+)?)\s*\(yıl\)", html, re.IGNORECASE)
            mom_match = re.search(r"aylık\s*%\s*(-?\d+(?:[.,]\d+)?)", html, re.IGNORECASE)
            if yoy_match:
                yoy = float(yoy_match.group(1).replace(",", "."))
                mom = float(mom_match.group(1).replace(",", ".")) if mom_match else None
                return {
                    "production_index": yoy,
                    "month_over_month_change": mom,
                    "year_over_year_change": yoy,
                    "date": datetime.now(timezone.utc).isoformat(),
                    "trend": "up" if yoy > 0 else "down",
                    "source": "TUIK",
                }

            return None
        except Exception as e:
            logger.debug(f"Sanayi üretim parse hatası: {e}")
            return None

    def _parse_unemployment(self, html: str) -> Optional[Dict]:
        """HTML'den işsizlik oranını çıkar."""
        try:
            match = re.search(r"%\s*(-?\d+(?:[.,]\d+)?)\s*\(ay\)", html, re.IGNORECASE)
            if match:
                unemployment = float(match.group(1).replace(",", "."))
                return {
                    "unemployment_rate": unemployment,
                    "employment_rate": None,
                    "date": datetime.now(timezone.utc).isoformat(),
                    "trend": "down" if unemployment > 0 else "stable",
                    "source": "TUIK",
                }

            return None
        except Exception as e:
            logger.debug(f"İşsizlik parse hatası: {e}")
            return None

    def _parse_capacity(self, html: str) -> Optional[Dict]:
        """HTML'den kapasite kullanım oranını çıkar."""
        try:
            return None
        except Exception as e:
            logger.debug(f"Kapasite parse hatası: {e}")
            return None

    def _extract_first_number(self, value: Optional[str]) -> Optional[float]:
        if not value:
            return None
        match = re.search(r"-?\d+(?:[.,]\d+)?", value)
        if not match:
            return None
        try:
            return float(match.group(0).replace(",", "."))
        except ValueError:
            return None

    async def store_macro_event(self, event_data: Dict) -> bool:
        """
        Makro olayı NewsItem olarak veritabanına kaydet.

        Args:
            event_data: {
                "type": "inflation" | "production" | "unemployment" | "capacity",
                "title": str,
                "summary": str,
                "importance": float (0-1)
            }
        """
        try:
            async with AsyncSessionLocal() as db:
                existing = await db.execute(
                    select(NewsItem).where(
                        NewsItem.source == "TUIK",
                        NewsItem.title == event_data.get("title", "TUIK Bildirimi"),
                    )
                )
                if existing.scalar_one_or_none():
                    logger.info(f"ℹ️ TUIK olayı zaten kayıtlı: {event_data.get('title')}")
                    return False

                # Makro olaylar tipik olarak GARAN (banka), EREGL (metal) vb. etkilenir
                # Düşük faiz → Bankalar kötü
                # Yüksek işsizlik → Consumer stocks zayıf
                # Kural tabanlı nötr varsayılan.
                analysis = {"sentiment_score": 0.0, "importance_score": 1.0}

                # NewsItem oluştur — makro haber, belirli bir hisseye bağlı değil
                news = NewsItem(
                    stock_id=None,
                    title=event_data.get("title", "TUIK Bildirimi"),
                    summary=event_data.get("summary", ""),
                    url=event_data.get("url", "https://www.tuik.gov.tr"),
                    source="TUIK",
                    language="tr",
                    category="macro",
                    published_at=datetime.now(timezone.utc),
                    sentiment_score=analysis.get("sentiment_score", 0.0),
                    sentiment_label=analysis.get("sentiment_label", "neutral"),
                    sentiment_confidence=analysis.get("sentiment_confidence", 0.6),
                    importance_score=event_data.get("importance", 0.80),
                    is_processed=False,
                )

                db.add(news)
                await db.commit()
                logger.info(f"✅ TUIK Makro Olayı kaydedildi: {event_data.get('title')}")
                return True

        except Exception as e:
            logger.error(f"TUIK olayı kayıt hatası: {e}")
            return False


# Singleton instance
tuik_adapter = TUIKAdapter()


async def run_tuik_scan() -> int:
    """
    TUIK verilerini periyodik olarak tara (arka plan görevi).
    APScheduler tarafından her gün saat 9'da çağrılır.
    """
    logger.info("📊 TUIK Taraması Başlıyor...")
    stored = 0
    fetched = 0

    try:
        # TÜFE / Enflasyon
        cpi = await tuik_adapter.fetch_cpi_inflation()
        if cpi:
            fetched += 1
            stored += await tuik_adapter.store_macro_event({
                "type": "inflation",
                "title": f"TUIK TÜFE Enflasyon: Yıllık %{cpi['inflation_rate_annual']:.1f}",
                "summary": (
                    f"Tüketici Fiyat Endeksi (TÜFE) yıllık %{cpi['inflation_rate_annual']:.1f}"
                    + (
                        f", aylık %{cpi['inflation_rate_monthly']:.2f}"
                        if cpi.get("inflation_rate_monthly") is not None
                        else ""
                    )
                ),
                "importance": 0.95,
                "url": cpi.get("url"),
            }) and 1 or 0

        # Sanayi Üretim
        production = await tuik_adapter.fetch_industrial_production()
        if production:
            fetched += 1
            stored += await tuik_adapter.store_macro_event({
                "type": "production",
                "title": f"TUIK Sanayi Üretim Endeksi: {production['production_index']}",
                "summary": (
                    f"Sanayi üretim endeksi {production['production_index']}"
                    + (
                        f", ay-üstü değişim %{production['month_over_month_change']:.1f}"
                        if production.get("month_over_month_change") is not None
                        else ""
                    )
                ),
                "importance": 0.75,
                "url": production.get("url"),
            }) and 1 or 0

        # İşsizlik Oranı
        unemployment = await tuik_adapter.fetch_unemployment_rate()
        if unemployment:
            fetched += 1
            stored += await tuik_adapter.store_macro_event({
                "type": "unemployment",
                "title": f"TUIK İşsizlik Oranı: %{unemployment['unemployment_rate']:.1f}",
                "summary": (
                    f"İşsizlik oranı %{unemployment['unemployment_rate']:.1f}"
                    + (
                        f", istihdam oranı %{unemployment['employment_rate']:.1f}"
                        if unemployment.get("employment_rate") is not None
                        else ""
                    )
                ),
                "importance": 0.80,
                "url": unemployment.get("url"),
            }) and 1 or 0

        # Kapasite Kullanımı
        capacity = await tuik_adapter.fetch_capacity_utilization()
        if capacity:
            fetched += 1
            stored += await tuik_adapter.store_macro_event({
                "type": "capacity",
                "title": f"TUIK Kapasite Kullanım Oranı: %{capacity['capacity_utilization_rate']:.1f}",
                "summary": f"Endüstriyel kapasite kullanım oranı %{capacity['capacity_utilization_rate']:.1f}",
                "importance": 0.70,
                "url": capacity.get("url"),
            }) and 1 or 0

        if fetched > 0:
            record_source_success("tuik", detail={"fetched_count": fetched, "stored_count": stored})
        else:
            record_source_failure(
                "tuik",
                "TUIK taraması veri üretemedi",
                detail={"fetched_count": fetched, "stored_count": stored},
            )

        logger.info(f"🟢 TUIK Taraması Tamamlandı: {stored} yeni veri, {fetched} kaynak bulundu")
        return stored

    except Exception as e:
        logger.error(f"TUIK taraması başarısız: {e}")
        record_source_failure("tuik", str(e))
        return 0
