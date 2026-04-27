"""Filesystem archive helpers for Borsa Istanbul Veri Store files."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

from app.services.bist_datastore_archive import get_latest_bist_datastore_snapshot


ARCHIVE_ROOT = Path(__file__).resolve().parents[2] / "runtime" / "bist_datastore"


def _safe_file_name(value: str) -> str:
    return value.replace("/", "_").replace("\\", "_").strip()


async def _download_file(url: str, target_path: Path) -> int:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=aiohttp.ClientTimeout(total=120),
        ) as response:
            response.raise_for_status()
            total_bytes = 0
            with target_path.open("wb") as handle:
                async for chunk in response.content.iter_chunked(1024 * 128):
                    handle.write(chunk)
                    total_bytes += len(chunk)
            return total_bytes


async def archive_latest_bist_datastore_files(
    *,
    category_code: str = "PPB",
    product_type_id: Optional[str] = None,
    limit: int = 5,
    overwrite: bool = False,
) -> Dict[str, Any]:
    snapshot = await get_latest_bist_datastore_snapshot(
        category_code=category_code,
        product_type_id=product_type_id,
        limit=limit,
    )
    snapshot_date = snapshot.get("snapshot_date")
    if not snapshot_date:
        return {
            "snapshot_date": None,
            "count": 0,
            "downloaded_count": 0,
            "skipped_count": 0,
            "items": [],
        }

    items: List[Dict[str, Any]] = []
    downloaded_count = 0
    skipped_count = 0
    failed_count = 0

    for item in snapshot.get("items", []) or []:
        file_name = _safe_file_name(str(item.get("file_name") or "unknown.bin"))
        product_type = str(item.get("product_type_id") or "unknown")
        target_path = ARCHIVE_ROOT / snapshot_date / product_type / file_name
        download_endpoint = str(item.get("download_endpoint") or "").strip()

        if not download_endpoint:
            skipped_count += 1
            items.append(
                {
                    **item,
                    "archived": False,
                    "archive_path": str(target_path),
                    "archive_status": "missing_download_endpoint",
                    "downloaded_bytes": 0,
                }
            )
            continue

        if target_path.exists() and not overwrite:
            skipped_count += 1
            items.append(
                {
                    **item,
                    "archived": True,
                    "archive_path": str(target_path),
                    "archive_status": "already_exists",
                    "downloaded_bytes": target_path.stat().st_size,
                }
            )
            continue

        try:
            downloaded_bytes = await _download_file(download_endpoint, target_path)
            downloaded_count += 1
            items.append(
                {
                    **item,
                    "archived": True,
                    "archive_path": str(target_path),
                    "archive_status": "downloaded",
                    "downloaded_bytes": downloaded_bytes,
                }
            )
        except Exception as exc:
            failed_count += 1
            items.append(
                {
                    **item,
                    "archived": False,
                    "archive_path": str(target_path),
                    "archive_status": "download_failed",
                    "downloaded_bytes": 0,
                    "error": str(exc),
                }
            )

    return {
        "snapshot_date": snapshot_date,
        "count": len(items),
        "downloaded_count": downloaded_count,
        "skipped_count": skipped_count,
        "failed_count": failed_count,
        "items": items,
    }


async def list_archived_bist_datastore_files(
    *,
    snapshot_date: Optional[str] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    if not ARCHIVE_ROOT.exists():
        return {
            "snapshot_date": snapshot_date,
            "count": 0,
            "items": [],
        }

    snapshot_dir = ARCHIVE_ROOT / snapshot_date if snapshot_date else None
    root = snapshot_dir if snapshot_dir and snapshot_dir.exists() else ARCHIVE_ROOT

    files = sorted(
        [path for path in root.rglob("*") if path.is_file()],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )[: max(1, min(limit, 200))]

    items = [
        {
            "file_name": path.name,
            "archive_path": str(path),
            "size_bytes": path.stat().st_size,
            "modified_at": path.stat().st_mtime,
            "snapshot_date": path.relative_to(ARCHIVE_ROOT).parts[0] if len(path.relative_to(ARCHIVE_ROOT).parts) >= 1 else None,
            "product_type_id": path.relative_to(ARCHIVE_ROOT).parts[1] if len(path.relative_to(ARCHIVE_ROOT).parts) >= 2 else None,
        }
        for path in files
    ]

    return {
        "snapshot_date": snapshot_date,
        "count": len(items),
        "items": items,
    }
