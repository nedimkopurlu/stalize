"""Hazine ve Maliye Bakanligi resmi yayin adaptoru.

Ilk iterasyonda HMB'nin butce, borclanma ve kamu finansmani odakli
duyuru/yayin sayfalarini on-demand tarar.
"""

from __future__ import annotations

import html
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class HMBAdapter:
    def __init__(self) -> None:
        self.base_url = "https://www.hmb.gov.tr"
        self.api_base_url = f"{self.base_url}/portal/v2"
        self.publication_urls = [
            f"{self.base_url}/duyurular",
            f"{self.base_url}/kamu-finansmani-istatistikleri",
            f"{self.base_url}/butce-gerceklesmeleri-raporlari",
        ]

    async def fetch_latest_publications(self, limit: int = 10) -> List[Dict]:
        headers = {"User-Agent": "Mozilla/5.0"}
        timeout = aiohttp.ClientTimeout(total=20)

        try:
            async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
                posts = await self._fetch_api_publications(session, limit=limit)
                if posts:
                    return posts

                for url in self.publication_urls:
                    html = await self._fetch_html(session, url)
                    if not html:
                        continue

                    publications = self._parse_publications(html, limit=limit)
                    if publications:
                        return publications
        except Exception as exc:
            logger.error(f"HMB yayin cekme hatasi: {exc}")

        return []

    async def _fetch_api_publications(self, session: aiohttp.ClientSession, limit: int = 10) -> List[Dict]:
        items: List[Dict] = []
        seen: set[str] = set()
        page = 1
        per_page = min(max(limit * 3, 20), 100)

        while len(items) < limit and page <= 3:
            payload = await self._fetch_json(session, f"{self.api_base_url}/posts?per_page={per_page}&page={page}")
            if not isinstance(payload, list) or not payload:
                break

            for post in payload:
                normalized = self._normalize_api_post(post)
                if not normalized:
                    continue

                dedupe_key = f"{normalized['title']}|{normalized['url']}"
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                items.append(normalized)

                if len(items) >= limit:
                    break
            page += 1

        return items[:limit]

    async def _fetch_html(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"HMB erisim hatasi ({url}): {response.status}")
                    return None
                return await response.text()
        except Exception as exc:
            logger.warning(f"HMB sayfa cekimi basarisiz ({url}): {exc}")
            return None

    async def _fetch_json(self, session: aiohttp.ClientSession, url: str) -> Any:
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"HMB API erisim hatasi ({url}): {response.status}")
                    return None
                return await response.json(content_type=None)
        except Exception as exc:
            logger.warning(f"HMB API cekimi basarisiz ({url}): {exc}")
            return None

    def _parse_publications(self, html: str, limit: int = 10) -> List[Dict]:
        soup = BeautifulSoup(html, "html.parser")
        publications: List[Dict] = []
        seen: set[str] = set()

        for link in soup.find_all("a", href=True):
            href = link["href"].strip()
            title = re.sub(r"\s+", " ", link.get_text(" ", strip=True))
            context = re.sub(r"\s+", " ", link.parent.get_text(" ", strip=True)) if link.parent else title
            haystack = f"{title} {context} {href}".lower()

            if not self._looks_relevant(haystack):
                continue

            absolute_url = urljoin(self.base_url, href)
            dedupe_key = f"{title}|{absolute_url}"
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            publications.append(
                {
                    "title": title or self._humanize_href(href),
                    "category": self._detect_category(haystack),
                    "published_on": self._extract_date(context) or self._extract_date(title),
                    "url": absolute_url,
                    "source": "HMB",
                }
            )

            if len(publications) >= limit:
                break

        return publications

    def _normalize_api_post(self, post: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        title = html.unescape(str(post.get("title", {}).get("rendered") or ""))
        title = re.sub(r"\s+", " ", title).strip()
        excerpt = re.sub(r"<[^>]+>", " ", str(post.get("excerpt", {}).get("rendered") or ""))
        excerpt = html.unescape(excerpt)
        excerpt = re.sub(r"\s+", " ", excerpt).strip()
        link = str(post.get("link") or "").strip()
        haystack = f"{title} {excerpt} {link}".lower()

        if not title or not self._looks_relevant(haystack):
            return None

        return {
            "title": title,
            "category": self._detect_category(haystack),
            "published_on": self._format_api_date(post.get("date")),
            "url": link,
            "source": "HMB",
        }

    def _looks_relevant(self, haystack: str) -> bool:
        negative_keywords = (
            "uzman yardimciligi",
            "giris sinavi",
            "personel",
            "kariyer",
            "basvuru",
            "staj",
        )
        if any(keyword in haystack for keyword in negative_keywords):
            return False

        keywords = (
            "butce",
            "borclanma",
            "finansman",
            "ihale",
            "kamu finansmani",
            "ic borc",
            "dis borc",
            "nakit gerceklesme",
            "hazine",
        )
        return any(keyword in haystack for keyword in keywords)

    def _detect_category(self, haystack: str) -> str:
        if "borclanma" in haystack or "ihale" in haystack or "borc" in haystack:
            return "borclanma"
        if "nakit" in haystack:
            return "nakit"
        if "kamu finansmani" in haystack or "finansman" in haystack:
            return "kamu_finansmani"
        return "butce"

    def _extract_date(self, text: str) -> Optional[str]:
        match = re.search(
            r"(\d{1,2}[./-]\d{1,2}[./-]\d{4}|\d{1,2}\s+[A-Za-zCIGOSUacgiosu]+\s+\d{4})",
            text,
            re.IGNORECASE,
        )
        return match.group(1) if match else None

    def _humanize_href(self, href: str) -> str:
        filename = href.rstrip("/").split("/")[-1]
        filename = re.sub(r"\.(pdf|xls|xlsx|doc|docx)$", "", filename, flags=re.IGNORECASE)
        filename = filename.replace("-", " ").replace("_", " ")
        return re.sub(r"\s+", " ", filename).strip()

    def _format_api_date(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value).strftime("%d.%m.%Y")
        except ValueError:
            return None


hmb_adapter = HMBAdapter()
