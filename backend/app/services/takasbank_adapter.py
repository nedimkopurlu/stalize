"""Takasbank resmi duyuru adaptörü."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class TakasbankAdapter:
    def __init__(self) -> None:
        self.base_url = "https://www.takasbank.com.tr"
        self.announcements_url = f"{self.base_url}/tr/duyurular"

    async def fetch_latest_announcements(self, limit: int = 10) -> List[Dict]:
        try:
            process = await asyncio.create_subprocess_exec(
                "curl",
                "-L",
                "-s",
                self.announcements_url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=20)
            if process.returncode != 0:
                logger.warning(f"Takasbank duyuru erişim hatası: {stderr.decode('utf-8', 'ignore').strip()}")
                return []

            html = stdout.decode("utf-8", "ignore")
            return self._parse_announcements(html, limit=limit)
        except TimeoutError:
            logger.error("Takasbank duyuru çekme hatası: zaman aşımı")
            return []
        except Exception as exc:
            logger.error(f"Takasbank duyuru çekme hatası: {exc}")
            return []

    def _parse_announcements(self, html: str, limit: int = 10) -> List[Dict]:
        soup = BeautifulSoup(html, "html.parser")
        announcements: List[Dict] = []
        seen: set[str] = set()

        for card in soup.select(".notifications-list .notification"):
            day_tag = card.select_one(".date .day")
            month_tag = card.select_one(".date .month")
            category_tag = card.select_one(".category")
            link_tag = card.select_one(".text a[href]")

            if not day_tag or not month_tag or not link_tag:
                continue

            href = link_tag.get("href", "").strip()
            headline = re.sub(r"\s+", " ", link_tag.get_text(" ", strip=True))
            category = re.sub(r"\s+", " ", category_tag.get_text(" ", strip=True)) if category_tag else None
            published_on = f"{day_tag.get_text(strip=True)} {month_tag.get_text(strip=True)}"
            url = urljoin(self.base_url, href)
            key = f"{published_on}|{headline}|{url}"

            if key in seen:
                continue
            seen.add(key)

            announcements.append(
                {
                    "published_on": published_on,
                    "headline": headline,
                    "category": category,
                    "url": url,
                    "source": "Takasbank",
                }
            )

            if len(announcements) >= limit:
                break

        return announcements

takasbank_adapter = TakasbankAdapter()
