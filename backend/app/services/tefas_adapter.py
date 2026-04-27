"""TEFAS resmi fon veri adaptörü.

Gerçek veri yalnızca resmi TEFAS sayfasından okunur. Fallback yoktur.
"""

from __future__ import annotations

import asyncio
import logging
import json
import re
from typing import Dict, List, Optional

import aiohttp
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class TefasAdapter:
    def __init__(self) -> None:
        self.base_url = "https://www.tefas.gov.tr"
        self._fund_type_labels = {
            "YAT": "Menkul Kıymet Yatırım Fonları",
            "EMK": "Emeklilik Fonları",
            "BYF": "Borsa Yatırım Fonları",
            "GYF": "Gayrimenkul Yatırım Fonları",
            "GSYF": "Girişim Sermayesi Yatırım Fonları",
        }

    async def fetch_fund_detail(self, fund_code: str) -> Optional[Dict]:
        fund_code = fund_code.strip().upper()
        if not fund_code:
            return None

        url = f"{self.base_url}/FonAnaliz.aspx?FonKod={fund_code}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as response:
                    if response.status != 200:
                        logger.warning(f"TEFAS erişim hatası [{fund_code}]: {response.status}")
                        return None

                    html = await response.text()
                    parsed = self._parse_fund_detail(html, fund_code, url)
                    return parsed
        except Exception as exc:
            logger.error(f"TEFAS veri çekme hatası [{fund_code}]: {exc}")
            return None

    async def fetch_fund_universe(self, fund_type: str = "YAT", limit: int = 100, start: int = 0) -> Dict:
        fund_type = fund_type.strip().upper()
        if fund_type not in self._fund_type_labels:
            return {"fund_type": fund_type, "fund_type_label": fund_type, "total": 0, "count": 0, "items": []}

        payload = {
            "draw": "1",
            "start": str(start),
            "length": str(limit),
            "calismatipi": "2",
            "fontip": fund_type,
            "sfontur": "",
            "kurucukod": "",
            "fongrup": "",
            "bastarih": "",
            "bittarih": "",
            "fonturkod": "",
            "fonunvantip": "",
            "strperiod": "1,1,1,1,1,1,1",
            "islemdurum": "",
        }

        try:
            curl_args = [
                "curl",
                "-s",
                f"{self.base_url}/api/DB/BindComparisonFundReturns",
                "-X",
                "POST",
                "-H",
                "X-Requested-With: XMLHttpRequest",
                "-H",
                "Content-Type: application/x-www-form-urlencoded; charset=UTF-8",
            ]
            for key, value in payload.items():
                curl_args.extend(["--data", f"{key}={value}"])

            process = await asyncio.create_subprocess_exec(
                *curl_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=20)
            if process.returncode != 0:
                logger.warning(f"TEFAS evren erişim hatası [{fund_type}]: {stderr.decode('utf-8', 'ignore').strip()}")
                return {
                    "fund_type": fund_type,
                    "fund_type_label": self._fund_type_labels[fund_type],
                    "total": 0,
                    "count": 0,
                    "items": [],
                }

            raw = json.loads(stdout.decode("utf-8", "ignore"))
            return self._normalize_fund_universe(raw, fund_type=fund_type, limit=limit)
        except TimeoutError:
            logger.error(f"TEFAS evren çekme hatası [{fund_type}]: zaman aşımı")
            return {
                "fund_type": fund_type,
                "fund_type_label": self._fund_type_labels.get(fund_type, fund_type),
                "total": 0,
                "count": 0,
                "items": [],
            }
        except Exception as exc:
            logger.error(f"TEFAS evren çekme hatası [{fund_type}]: {exc}")
            return {
                "fund_type": fund_type,
                "fund_type_label": self._fund_type_labels.get(fund_type, fund_type),
                "total": 0,
                "count": 0,
                "items": [],
            }

    async def fetch_all_fund_universes(self, limit_per_type: int = 100) -> Dict:
        universes: List[Dict] = []
        total = 0

        for fund_type in self._fund_type_labels:
            universe = await self.fetch_fund_universe(fund_type=fund_type, limit=limit_per_type)
            universes.append(universe)
            total += universe["count"]

        return {
            "fund_types": universes,
            "count": total,
            "type_count": len(universes),
        }

    def _parse_fund_detail(self, html: str, fund_code: str, url: str) -> Optional[Dict]:
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True)

        if fund_code not in text.upper():
            return None

        fund_name = self._extract_fund_name(soup, fund_code)

        return {
            "fund_code": fund_code,
            "fund_name": fund_name,
            "url": url,
            "price": self._extract_metric(text, ["Son Fiyat", "Birim Pay Değeri"]),
            "daily_change_pct": self._extract_metric(text, ["Günlük Getiri", "Günlük Değişim"]),
            "investor_count": self._extract_integer(text, ["Yatırımcı Sayısı"]),
            "risk_value": self._extract_integer(text, ["Risk Değeri"]),
            "one_month_return_pct": self._extract_metric(text, ["1 Ay", "1 Aylık"]),
            "three_month_return_pct": self._extract_metric(text, ["3 Ay", "3 Aylık"]),
            "six_month_return_pct": self._extract_metric(text, ["6 Ay", "6 Aylık"]),
            "one_year_return_pct": self._extract_metric(text, ["1 Yıl", "1 Yıllık"]),
        }

    def _extract_fund_name(self, soup: BeautifulSoup, fund_code: str) -> str:
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        normalized_title = re.sub(r"\s+", " ", title)
        if fund_code in normalized_title.upper():
            return normalized_title

        headings = soup.find_all(["h1", "h2", "h3", "span", "div"])
        for tag in headings:
            value = re.sub(r"\s+", " ", tag.get_text(" ", strip=True))
            if fund_code in value.upper() and len(value) > len(fund_code):
                return value

        return fund_code

    def _extract_metric(self, text: str, labels: list[str]) -> Optional[float]:
        for label in labels:
            pattern = rf"{re.escape(label)}\s*[:\-]?\s*([\-+]?\d+[.,]?\d*)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(",", "."))
                except ValueError:
                    return None
        return None

    def _extract_integer(self, text: str, labels: list[str]) -> Optional[int]:
        value = self._extract_metric(text, labels)
        if value is None:
            return None
        return int(round(value))

    def _normalize_fund_universe(self, payload: Dict, fund_type: str, limit: Optional[int] = None) -> Dict:
        items = []
        for row in payload.get("data", []) or []:
            items.append(
                {
                    "fund_code": row.get("FONKODU"),
                    "fund_name": row.get("FONUNVAN"),
                    "umbrella_type": row.get("FONTURACIKLAMA"),
                    "one_month_return_pct": row.get("GETIRI1A"),
                    "three_month_return_pct": row.get("GETIRI3A"),
                    "six_month_return_pct": row.get("GETIRI6A"),
                    "year_to_date_return_pct": row.get("GETIRIYB"),
                    "one_year_return_pct": row.get("GETIRI1Y"),
                    "three_year_return_pct": row.get("GETIRI3Y"),
                    "five_year_return_pct": row.get("GETIRI5Y"),
                    "detail_url": f"{self.base_url}/FonAnaliz.aspx?FonKod={row.get('FONKODU')}",
                    "source": "TEFAS",
                }
            )

        if limit is not None and limit >= 0:
            items = items[:limit]

        return {
            "fund_type": fund_type,
            "fund_type_label": self._fund_type_labels.get(fund_type, fund_type),
            "total": int(payload.get("recordsTotal") or len(items)),
            "count": len(items),
            "items": items,
        }


tefas_adapter = TefasAdapter()
