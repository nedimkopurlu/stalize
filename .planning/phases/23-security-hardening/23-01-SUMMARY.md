---
phase: 23
plan: 1
title: Security Hardening — SEC-01 through SEC-04
status: complete
completed: "2026-04-28"
---

# Phase 23 — Security Hardening: Summary

## What Was Done

All four security requirements (SEC-01–SEC-04) implemented inline across backend API layer.

### SEC-01: API Key Authentication on Mutation Endpoints

Created `backend/app/core/security.py` with `verify_api_key` FastAPI dependency:
- Returns immediately if `settings.API_KEY` is `None` (backward-compatible dev mode)
- Returns HTTP 401 if `X-Api-Key` header is missing or wrong

Applied `_: None = Depends(verify_api_key)` to every POST/DELETE endpoint:
- `stocks.py`: `run_technical_analysis`, `update_all_scores`
- `portfolio_v2.py`: `add_position`, `close_position`, `add_change_log`
- `macro.py`: `trigger_tcmb_scan`, `trigger_tuik_scan`
- `admin.py`: `trigger_source_scan`, `backfill_bist_datastore_snapshot`, `archive_bist_datastore_latest_files`, `trigger_kap_scan`
- `model_portfolio.py`: `model_portfolio_generate`, `model_portfolio_snapshot`

### SEC-02: CORS Wildcard Origin Fix

`main.py` — Changed default from allow all origins to `localhost:3000` only:
```python
_cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
_allow_credentials = "*" not in _origins  # prevents CSRF with wildcard + credentials
```

### SEC-03: Error Detail Sanitization

Replaced all `str(e)` / `detail=str(e)` in HTTP responses with generic Turkish messages:
- `intelligence.py`: 5 occurrences replaced; `exc_info=True` added to all `logger.error()` calls
- `macro.py`: `get_macro_indicators` exception handler uses generic message

### SEC-04: DEBUG=False Default

`config.py`:
- `DEBUG: bool = False` (was `True`)
- `API_KEY: Optional[str] = None` added

Database.py already uses `echo=settings.DEBUG`, so SQL echo is now off by default.

## Files Changed

- `backend/app/core/security.py` (NEW)
- `backend/app/core/config.py`
- `backend/app/main.py`
- `backend/app/api/stocks.py`
- `backend/app/api/portfolio_v2.py`
- `backend/app/api/macro.py`
- `backend/app/api/admin.py`
- `backend/app/api/model_portfolio.py`
- `backend/app/api/intelligence.py`

## Acceptance Criteria Status

- [x] SEC-01: API key olmadan POST/DELETE endpoint'leri 401 döner; `API_KEY=None` ise bypass (dev mode)
- [x] SEC-02: CORS wildcard origin kaldırıldı; `allow_credentials` wildcard ile birleşmiyor
- [x] SEC-03: `str(e)` HTTP response'lardan temizlendi; detay yalnızca server log'da
- [x] SEC-04: `DEBUG=False` varsayılan; SQL echo kapalı
