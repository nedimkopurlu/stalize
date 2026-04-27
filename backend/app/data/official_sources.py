"""Resmi kaynak kataloğu.

Faz 3 omurgasında hangi resmi kaynağın üretimde aktif, hangisinin sırada olduğunu
tek yerden yönetmek için kullanılır.
"""

from __future__ import annotations

from typing import Dict, List


OFFICIAL_SOURCE_CATALOG: List[Dict[str, str]] = [
    {"key": "kap", "name": "KAP", "url": "https://www.kap.org.tr", "category": "company_disclosure", "ingest_status": "active", "priority": "tier1", "scan_mode": "scheduler+manual", "cadence": "continuous", "warn_after_hours": "12", "status_note": "Canlı RSS taraması bağlı"},
    {"key": "borsa_istanbul", "name": "Borsa İstanbul", "url": "https://www.borsaistanbul.com", "category": "exchange", "ingest_status": "active", "priority": "tier1", "scan_mode": "scheduler+manual", "cadence": "daily", "warn_after_hours": "168", "status_note": "Duyuru adaptörü artık ingest registry ve scheduler'a bağlı", "api_endpoint": "/api/sources/borsa-istanbul/announcements"},
    {"key": "bist_datastore", "name": "Borsa İstanbul Veri Store", "url": "https://datastore.borsaistanbul.com", "category": "exchange_data", "ingest_status": "active", "priority": "tier1", "scan_mode": "scheduler+manual", "cadence": "daily", "warn_after_hours": "168", "status_note": "Katalog, metadata snapshot ve runtime dosya arşivi aktif", "api_endpoint": "/api/sources/bist-datastore/catalog"},
    {"key": "tcmb", "name": "TCMB", "url": "https://www.tcmb.gov.tr", "category": "macro", "ingest_status": "active", "priority": "tier1", "scan_mode": "scheduler+manual", "cadence": "event_driven", "warn_after_hours": "72", "status_note": "Makro tarama aktif"},
    {"key": "tuik", "name": "TÜİK", "url": "https://www.tuik.gov.tr", "category": "macro", "ingest_status": "active", "priority": "tier1", "scan_mode": "scheduler+manual", "cadence": "calendar_based", "warn_after_hours": "168", "status_note": "Makro tarama aktif"},
    {"key": "hmb", "name": "Hazine ve Maliye Bakanlığı", "url": "https://www.hmb.gov.tr", "category": "fiscal", "ingest_status": "active", "priority": "tier2", "scan_mode": "scheduler+manual", "cadence": "weekly", "warn_after_hours": "168", "status_note": "Bütçe/borçlanma yayın adaptörü kalıcı ingest ve scheduler'a bağlı", "api_endpoint": "/api/sources/hmb/publications"},
    {"key": "mkk", "name": "MKK", "url": "https://www.mkk.com.tr", "category": "custody", "ingest_status": "active", "priority": "tier2", "scan_mode": "scheduler+manual", "cadence": "monthly", "warn_after_hours": "720", "status_note": "Aylık piyasa bültenleri kalıcı ingest ve scheduler'a bağlı", "api_endpoint": "/api/sources/mkk/monthly-bulletins"},
    {"key": "takasbank", "name": "Takasbank", "url": "https://www.takasbank.com.tr", "category": "settlement", "ingest_status": "active", "priority": "tier2", "scan_mode": "scheduler+manual", "cadence": "weekly", "warn_after_hours": "168", "status_note": "Resmi duyurular kalıcı ingest ve scheduler'a bağlı", "api_endpoint": "/api/sources/takasbank/announcements"},
    {"key": "tefas", "name": "TEFAS", "url": "https://www.tefas.gov.tr", "category": "funds", "ingest_status": "active", "priority": "tier2", "scan_mode": "scheduler+manual", "cadence": "daily", "warn_after_hours": "168", "status_note": "Fon detayı ve fon evreni adaptörleri aktif", "api_endpoint": "/api/sources/tefas/universe"},
]


def get_official_source_keys() -> List[str]:
    return [item["key"] for item in OFFICIAL_SOURCE_CATALOG]


def get_official_source_map() -> Dict[str, Dict[str, str]]:
    return {item["key"]: item for item in OFFICIAL_SOURCE_CATALOG}
