"""Persistence helpers for Borsa Istanbul Veri Store file metadata."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal
from app.models.bist_datastore import BistDatastoreFileSnapshot
from app.services.bist_datastore_adapter import bist_datastore_adapter
from app.services.source_health import record_source_failure, record_source_success


def _parse_datastore_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    value = str(value).strip()
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


async def persist_bist_datastore_snapshot(
    *,
    category_code: str = "PPB",
    dataset_limit: int = 20,
    files_per_dataset: int = 5,
    snapshot_date: Optional[date] = None,
) -> Dict[str, Any]:
    snapshot_date = snapshot_date or date.today()
    category_code = category_code.strip().upper()
    dataset_limit = max(1, min(dataset_limit, 100))
    files_per_dataset = max(1, min(files_per_dataset, 50))

    datasets = await bist_datastore_adapter.fetch_dataset_catalog(limit=dataset_limit, category_code=category_code)
    if not datasets:
        record_source_failure(
            "bist_datastore",
            "No datasets returned from public datastore catalog",
            detail={"category_code": category_code, "dataset_limit": dataset_limit, "files_per_dataset": files_per_dataset},
        )
        return {
            "snapshot_date": snapshot_date.isoformat(),
            "category_code": category_code,
            "dataset_count": 0,
            "stored_count": 0,
            "items": [],
        }

    rows: List[BistDatastoreFileSnapshot] = []
    items: List[Dict[str, Any]] = []

    for dataset in datasets:
        product_type_id = str(dataset.get("product_type_id") or "").strip()
        if not product_type_id:
            continue

        payload = await bist_datastore_adapter.fetch_product_files(
            product_type_id=product_type_id,
            page=1,
            page_size=files_per_dataset,
        )
        for item in payload.get("items", []) or []:
            file_id = str(item.get("id") or "").strip()
            file_name = str(item.get("file_name") or "").strip()
            if not file_id or not file_name:
                continue

            row_payload = {
                "snapshot_date": snapshot_date,
                "category_code": category_code,
                "market": dataset.get("market"),
                "market_key": dataset.get("market_key"),
                "dataset_code": dataset.get("dataset_code"),
                "dataset_title": dataset.get("title"),
                "product_type_id": product_type_id,
                "file_id": file_id,
                "file_name": file_name,
                "file_date": _parse_datastore_date(item.get("date")),
                "create_date": _parse_datastore_date(item.get("create_date")),
                "file_size": item.get("file_size"),
                "access_type": item.get("access_type") or dataset.get("access_type"),
                "update_frequency": dataset.get("update_frequency"),
                "download_endpoint": item.get("download_endpoint"),
                "catalog_url": dataset.get("catalog_url"),
                "datastore_url": dataset.get("datastore_url"),
                "source": "Borsa İstanbul Veri Store",
            }
            rows.append(BistDatastoreFileSnapshot(**row_payload))
            items.append(
                {
                    **row_payload,
                    "snapshot_date": snapshot_date.isoformat(),
                    "file_date": row_payload["file_date"].isoformat() if row_payload["file_date"] else None,
                    "create_date": row_payload["create_date"].isoformat() if row_payload["create_date"] else None,
                }
            )

    async with AsyncSessionLocal() as db:
        await db.execute(
            delete(BistDatastoreFileSnapshot).where(
                BistDatastoreFileSnapshot.snapshot_date == snapshot_date,
                BistDatastoreFileSnapshot.category_code == category_code,
            )
        )
        db.add_all(rows)
        await db.commit()

    record_source_success(
        "bist_datastore",
        detail={
            "category_code": category_code,
            "dataset_count": len(datasets),
            "stored_count": len(rows),
            "files_per_dataset": files_per_dataset,
        },
    )

    return {
        "snapshot_date": snapshot_date.isoformat(),
        "category_code": category_code,
        "dataset_count": len(datasets),
        "stored_count": len(rows),
        "items": items,
    }


async def get_latest_bist_datastore_snapshot(
    *,
    category_code: Optional[str] = None,
    product_type_id: Optional[str] = None,
    limit: int = 100,
) -> Dict[str, Any]:
    limit = max(1, min(limit, 500))
    async with AsyncSessionLocal() as db:
        latest_date_query = select(BistDatastoreFileSnapshot.snapshot_date)
        if category_code:
            latest_date_query = latest_date_query.where(
                BistDatastoreFileSnapshot.category_code == category_code.strip().upper()
            )
        latest_date = await db.scalar(latest_date_query.order_by(BistDatastoreFileSnapshot.snapshot_date.desc()).limit(1))
        if latest_date is None:
            return {"snapshot_date": None, "count": 0, "items": []}

        query = select(BistDatastoreFileSnapshot).where(BistDatastoreFileSnapshot.snapshot_date == latest_date)
        if category_code:
            query = query.where(BistDatastoreFileSnapshot.category_code == category_code.strip().upper())
        if product_type_id:
            query = query.where(BistDatastoreFileSnapshot.product_type_id == str(product_type_id).strip())

        query = query.order_by(
            BistDatastoreFileSnapshot.product_type_id.asc(),
            BistDatastoreFileSnapshot.file_date.desc().nullslast(),
            BistDatastoreFileSnapshot.file_name.asc(),
        ).limit(limit)

        rows = (await db.execute(query)).scalars().all()

    items = [
        {
            "category_code": row.category_code,
            "market": row.market,
            "market_key": row.market_key,
            "dataset_code": row.dataset_code,
            "dataset_title": row.dataset_title,
            "product_type_id": row.product_type_id,
            "file_id": row.file_id,
            "file_name": row.file_name,
            "file_date": row.file_date.isoformat() if row.file_date else None,
            "create_date": row.create_date.isoformat() if row.create_date else None,
            "file_size": row.file_size,
            "access_type": row.access_type,
            "update_frequency": row.update_frequency,
            "download_endpoint": row.download_endpoint,
            "catalog_url": row.catalog_url,
            "datastore_url": row.datastore_url,
            "source": row.source,
        }
        for row in rows
    ]

    return {
        "snapshot_date": latest_date.isoformat(),
        "count": len(items),
        "items": items,
    }
