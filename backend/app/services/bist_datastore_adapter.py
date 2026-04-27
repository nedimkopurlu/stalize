"""Borsa İstanbul Veri Store katalog adaptörü.

Gerçek Veri Store API uçlarını kullanarak kategori, ürün tipi ve örnek ürün
verisini tek bir normalize katalog listesine indirger.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import aiohttp


logger = logging.getLogger(__name__)


class BistDatastoreAdapter:
    def __init__(self) -> None:
        self.base_url = "https://datastore.borsaistanbul.com"
        self._market_labels = {
            "PPB": ("Pay Piyasası", "pay_piyasasi"),
            "BAPB": ("Borçlanma Araçları Piyasası", "borclanma_araclari"),
            "VIOP": ("Vadeli İşlem ve Opsiyon Piyasası", "viop"),
            "KMTPB": ("Kıymetli Madenler ve Taşlar Piyasası", "kiymetli_madenler"),
            "ENDEKS": ("Endeks Verileri", "endeks"),
        }

    async def fetch_dataset_catalog(self, limit: int = 20, category_code: str = "PPB") -> List[Dict]:
        category_code = category_code.strip().upper()
        product_types = await self._fetch_product_types(category_code=category_code, limit=max(limit, 1))
        if not product_types:
            return []

        datasets: List[Dict] = []
        seen: set[str] = set()

        for product_type in product_types:
            products = await self._fetch_products(product_type_id=str(product_type["id"]), page=1, page_size=1)
            latest_product = products[0] if products else {}

            key = f"{product_type.get('id')}|{product_type.get('name')}"
            if key in seen:
                continue
            seen.add(key)

            market_label, market_key = self._get_market_info(
                str(product_type.get("data_parent_group") or category_code)
            )
            access_type = str(product_type.get("access_type") or "").upper()

            datasets.append(
                {
                    "title": product_type.get("name"),
                    "market": market_label,
                    "market_key": market_key,
                    "dataset_code": product_type.get("code"),
                    "product_type_id": product_type.get("id"),
                    "subscription_product": product_type.get("subscription_product"),
                    "price": product_type.get("price"),
                    "access_type": access_type,
                    "update_frequency": self._translate_period(product_type.get("period")),
                    "latest_file_name": latest_product.get("file_name"),
                    "latest_file_date": latest_product.get("date"),
                    "latest_create_date": latest_product.get("create_date"),
                    "latest_file_size": latest_product.get("file_size"),
                    "download_endpoint": latest_product.get("download_endpoint"),
                    "catalog_url": f"{self.base_url}/api/product-type/{product_type.get('id')}/products?page=1&page-size=1",
                    "datastore_url": self.base_url,
                    "source": "Borsa İstanbul Veri Store",
                }
            )
            if len(datasets) >= limit:
                break

        return datasets

    async def fetch_product_files(self, product_type_id: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        product_type_id = str(product_type_id).strip()
        if not product_type_id:
            return {
                "product_type_id": None,
                "count": 0,
                "page": page,
                "page_size": page_size,
                "items": [],
            }

        products = await self._fetch_products(product_type_id=product_type_id, page=page, page_size=page_size)
        return {
            "product_type_id": product_type_id,
            "count": len(products),
            "page": page,
            "page_size": page_size,
            "items": products,
        }

    async def probe_file_download(self, file_id: str) -> Dict[str, Any]:
        file_id = str(file_id).strip()
        if not file_id:
            return {
                "file_id": None,
                "download_url": None,
                "http_status": None,
                "reachable": False,
                "headers": {},
            }

        path = f"/api/file/{file_id}"
        url = f"{self.base_url}{path}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=aiohttp.ClientTimeout(total=20),
                    allow_redirects=False,
                ) as response:
                    headers = {
                        key.lower(): value
                        for key, value in response.headers.items()
                        if key.lower() in {"content-type", "content-length", "location"}
                    }
                    return {
                        "file_id": file_id,
                        "download_url": url,
                        "http_status": response.status,
                        "reachable": response.status in {200, 302, 303, 307, 308},
                        "headers": headers,
                    }
        except Exception as exc:
            logger.error("BIST datastore file probe hatası [%s]: %s", file_id, exc)
            return {
                "file_id": file_id,
                "download_url": url,
                "http_status": None,
                "reachable": False,
                "headers": {},
                "error": str(exc),
            }

    async def _fetch_product_types(self, category_code: str, limit: int) -> List[Dict]:
        payload = await self._get_json(f"/api/product-type?category={category_code}")
        if not isinstance(payload, list):
            return []

        items: List[Dict] = []
        for item in payload[:limit]:
            items.append(
                {
                    "id": item.get("id"),
                    "code": item.get("code"),
                    "name": item.get("name"),
                    "period": item.get("period"),
                    "price": item.get("price"),
                    "access_type": item.get("accessType"),
                    "subscription_product": item.get("subscriptionProduct"),
                    "data_parent_group": item.get("dataParentGroup"),
                    "data_group": item.get("dataGroup"),
                    "data_sub_group": item.get("dataSubGroup"),
                }
            )
        return items

    async def _fetch_products(self, product_type_id: str, page: int, page_size: int) -> List[Dict]:
        payload = await self._get_json(
            f"/api/product-type/{product_type_id}/products?page={page}&page-size={page_size}"
        )
        if not isinstance(payload, list):
            return []

        items: List[Dict] = []
        for item in payload:
            items.append(
                {
                    "id": item.get("id"),
                    "file_name": item.get("fileName"),
                    "date": item.get("date"),
                    "create_date": item.get("createDate"),
                    "file_size": item.get("fileSize"),
                    "price": item.get("price"),
                    "discount_price": item.get("discountPrice"),
                    "in_library": item.get("inLibrary"),
                    "period": item.get("dataDefnEntity", {}).get("period"),
                    "market": item.get("dataDefnEntity", {}).get("market"),
                    "access_type": item.get("dataDefnEntity", {}).get("accessType"),
                    "source_system": item.get("dataDefnEntity", {}).get("sourceSystem"),
                    "download_endpoint": f"{self.base_url}/api/file/{item.get('id')}",
                }
            )
        return items

    async def _get_json(self, path: str) -> Optional[object]:
        url = f"{self.base_url}{path}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=20),
                ) as response:
                    if response.status != 200:
                        logger.warning("BIST datastore erişim hatası [%s]: %s", path, response.status)
                        return None
                    return await response.json(content_type=None)
        except Exception as exc:
            logger.error("BIST datastore veri çekme hatası [%s]: %s", path, exc)
            return None

    def _get_market_info(self, code: str) -> Tuple[str, str]:
        return self._market_labels.get(code, (code, code.lower()))

    def _translate_period(self, period: Optional[str]) -> str:
        mapping = {
            "G": "Günlük",
            "A": "Aylık",
            "Y": "Yıllık",
            "S": "Seanslık",
            "H": "Saatlik",
            "D": "Dönemsel",
        }
        return mapping.get(str(period or "").upper(), "Belirtilmemiş")


bist_datastore_adapter = BistDatastoreAdapter()
