"""Borsa İstanbul resmi duyuru adaptörü."""

from __future__ import annotations

import logging
import re
from typing import Dict, List

import aiohttp
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class BorsaAnnouncementsAdapter:
    def __init__(self) -> None:
        self.base_url = "https://www.borsaistanbul.com"
        self.announcements_url = f"{self.base_url}/duyurular-eski"

    async def fetch_latest_announcements(self, limit: int = 10) -> List[Dict]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.announcements_url,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Borsa İstanbul duyuru erişim hatası: {response.status}")
                        return []

                    html = await response.text()
                    return self._parse_announcements(html, limit=limit)
        except Exception as exc:
            logger.error(f"Borsa İstanbul duyuru çekme hatası: {exc}")
            return []

    def _parse_announcements(self, html: str, limit: int = 10) -> List[Dict]:
        soup = BeautifulSoup(html, "html.parser")
        text_nodes = [node.get_text(" ", strip=True) for node in soup.find_all(["a", "li", "div", "p"])]
        pattern = re.compile(r"^(\d{1,2}\s+[A-Za-zÇĞİÖŞÜçğıöşü]+\s+\d{4})\s+(.+)$")
        date_pattern = re.compile(r"\d{1,2}\s+[A-Za-zÇĞİÖŞÜçğıöşü]+\s+\d{4}")

        announcements: List[Dict] = []
        seen = set()
        for node_text in text_nodes:
            normalized = re.sub(r"\s+", " ", node_text).strip()
            if len(date_pattern.findall(normalized)) != 1:
                continue
            match = pattern.match(normalized)
            if not match:
                continue

            published_on = match.group(1)
            headline = match.group(2)
            key = (published_on, headline)
            if key in seen:
                continue
            seen.add(key)

            announcements.append(
                {
                    "published_on": published_on,
                    "headline": headline,
                    "source": "Borsa İstanbul",
                    "url": self.announcements_url,
                }
            )
            if len(announcements) >= limit:
                break

        return announcements
borsa_announcements_adapter = BorsaAnnouncementsAdapter()
