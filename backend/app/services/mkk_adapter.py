"""MKK resmi piyasa bülteni adaptörü.

Gerçek veri yalnızca MKK resmi bülten sayfasından okunur. Fallback yoktur.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class MKKAdapter:
    def __init__(self) -> None:
        self.base_url = "https://www.mkk.com.tr"
        self.bulletins_url = f"{self.base_url}/veri-hizmetleri/mkk-aylik-piyasa-bulteni"

    async def fetch_latest_bulletins(self, limit: int = 10) -> List[Dict]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.bulletins_url,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as response:
                    if response.status != 200:
                        logger.warning(f"MKK bülten erişim hatası: {response.status}")
                        return []

                    html = await response.text()
                    return self._parse_bulletins(html, limit=limit)
        except Exception as exc:
            logger.error(f"MKK bülten çekme hatası: {exc}")
            return []

    def _parse_bulletins(self, html: str, limit: int = 10) -> List[Dict]:
        soup = BeautifulSoup(html, "html.parser")
        bulletins: List[Dict] = []
        seen_urls: set[str] = set()

        for link in soup.find_all("a", href=True):
            href = link["href"].strip()
            link_text = re.sub(r"\s+", " ", link.get_text(" ", strip=True))
            normalized_href = href.lower()
            normalized_text = link_text.lower()

            if not normalized_href.endswith(".pdf"):
                continue

            if "mkk-aylik-piyasa-bulteni" not in normalized_href and "mkk aylık piyasa bülteni" not in normalized_text:
                continue

            absolute_url = urljoin(self.base_url, href)
            if absolute_url in seen_urls:
                continue
            seen_urls.add(absolute_url)

            title = link_text or self._humanize_filename(href)
            bulletins.append(
                {
                    "title": title,
                    "period": self._extract_period(title, href),
                    "url": absolute_url,
                    "source": "MKK",
                }
            )

            if len(bulletins) >= limit:
                break

        return bulletins

    def _extract_period(self, title: str, href: str) -> Optional[str]:
        haystack = f"{title} {href}"
        match = re.search(
            r"(Ocak|Şubat|Subat|Mart|Nisan|Mayıs|Mayis|Haziran|Temmuz|Ağustos|Agustos|Eylül|Eylul|Ekim|Kasım|Kasim|Aralık|Aralik)\s+(\d{4})",
            haystack,
            re.IGNORECASE,
        )
        if not match:
            return None

        month = self._normalize_turkish_month(match.group(1))
        year = match.group(2)
        return f"{month} {year}"

    def _normalize_turkish_month(self, month: str) -> str:
        mapping = {
            "subat": "Şubat",
            "mayis": "Mayıs",
            "agustos": "Ağustos",
            "eylul": "Eylül",
            "kasim": "Kasım",
            "aralik": "Aralık",
        }
        lowered = month.lower()
        if lowered in mapping:
            return mapping[lowered]
        return month[:1].upper() + month[1:]

    def _humanize_filename(self, href: str) -> str:
        filename = href.rstrip("/").split("/")[-1]
        filename = re.sub(r"\.pdf$", "", filename, flags=re.IGNORECASE)
        filename = filename.replace("-", " ")
        return re.sub(r"\s+", " ", filename).strip()

mkk_adapter = MKKAdapter()
