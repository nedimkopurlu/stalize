---
phase: 38-portf-y-takip-listesi
plan: "01"
subsystem: portfolio
tags: [portfolio, close-position, realized-pnl, alembic, fastapi, react]
dependency_graph:
  requires: []
  provides:
    - PATCH /portfolio/positions/{id}/close — pozisyon kapatma endpoint
    - GET /portfolio/positions — açık + 30 günlük kapalı pozisyonlar
    - realized_pnl hesaplama ve kalıcı kayıt
  affects:
    - frontend portfolio page
    - portfolio_positions DB tablosu
tech_stack:
  added:
    - Alembic migration 004 (exit_price, exit_date, realized_pnl)
  patterns:
    - PATCH endpoint with Pydantic PositionClose model
    - OR/AND SQLAlchemy filter for mixed active/closed query
    - dependency_overrides pattern for FastAPI test mocking
key_files:
  created:
    - backend/alembic/versions/004_portfolio_position_close_fields.py
    - backend/tests/test_portfolio_close.py
  modified:
    - backend/app/models/portfolio_v2.py
    - backend/app/api/portfolio_v2.py
    - frontend/src/lib/api.ts
    - frontend/src/app/portfolio/page.tsx
    - frontend/src/app/portfolio/page.module.css
decisions:
  - Closed positions skip yfinance fetch in GET — no need for current_price on exited positions
  - activePositions (not all positions) used for portfolio value, weight, and risk calculations
  - RecentTransactions also filtered to activePositions only
  - verify_api_key in dev returns None when API_KEY not configured; test uses wrong-key path to verify 401
metrics:
  duration_minutes: 20
  completed_date: "2026-05-08"
  tasks_completed: 5
  files_modified: 7
---

# Phase 38 Plan 01: PORT-02 Pozisyon Kapatma + Gerçek K/Z Summary

## One-liner

PATCH /portfolio/positions/{id}/close endpoint with Alembic migration, realized_pnl = (exit_price - entry_price) * quantity, and inline Kapat form + Geçmiş Pozisyonlar table in frontend.

## What Was Built

PORT-02 pozisyon kapatma özelliği uçtan uca implemente edildi:

- **DB Migration 004**: `portfolio_positions` tablosuna `exit_price`, `exit_date`, `realized_pnl` (nullable Float/Date/Float) eklendi. `alembic current` → `004 (head)`.
- **ORM update**: `PortfolioPosition` modeline 3 nullable kolon eklendi.
- **Backend GET update**: `/portfolio/positions` artık açık pozisyonları + son 30 günde kapatılanları (OR/AND SQLAlchemy filtresi) döner. Kapalı pozisyonlar için yfinance çağrısı yapılmaz. Response'a `is_active`, `exit_price`, `exit_date`, `realized_pnl` eklendi.
- **Backend PATCH endpoint**: `PATCH /portfolio/positions/{id}/close` — `PositionClose` Pydantic modeli, `_validate_positive_number` doğrulaması, `realized_pnl = round((exit_price - entry_price) * quantity, 4)`, `PortfolioChangeLog` "REMOVE" kaydı.
- **Backend tests** (5/5): success + realized_pnl calc, not-found 404, wrong API key 401, exit_price=0 → 422. Tüm testler geçiyor.
- **Frontend API**: `PortfolioPosition` interface'ine 4 yeni alan eklendi. `api.closePosition(id, data)` metodu eklendi.
- **Frontend UI**: `activePositions`/`closedPositions` türetme, `handleClosePosition`, inline Kapat butonu + exit_price/exit_date form, "Geçmiş Pozisyonlar" tablosu (realized_pnl TL + %).
- **Frontend CSS**: `.closeBtn`, `.closeForm`, `.closeInput`, `.closeConfirm`, `.closeCancel` stilleri eklendi.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | DB migration + ORM update | 1b2e9d0 | 2 files |
| 2 | Backend GET update + PATCH close endpoint | 9e57220 | 1 file |
| 3 | Backend tests | 454c1b1 | 1 file |
| 4 | Frontend API interface + closePosition | 5f2cfb4 | 1 file |
| 5 | Frontend UI: Kapat butonu + Geçmiş tablosu + CSS | a5d5c30 | 2 files |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] verify_api_key passes through in dev when API_KEY not set**
- **Found during**: Task 3
- **Issue**: `verify_api_key` returns `None` (no rejection) when `settings.API_KEY is None` and environment is not prod. Test for "no API key → 401/403" returned 404 instead.
- **Fix**: Replaced `test_close_position_no_api_key` with `test_close_position_wrong_api_key` — temporarily sets `cfg.settings.API_KEY` to a real value, sends wrong key, expects 401.
- **Files modified**: `backend/tests/test_portfolio_close.py`
- **Commit**: 454c1b1

None of the other deviations from plan spec: plan called for `updated_at` write in PATCH, but `PortfolioPosition.updated_at` uses SQLAlchemy `onupdate=func.now()` which triggers automatically on commit — explicit assignment omitted (not needed).

## Known Stubs

None — all data is wired end-to-end: realized_pnl is computed from real DB values and displayed in the Geçmiş Pozisyonlar table.

## Self-Check

### Files created/exist

- [x] `backend/alembic/versions/004_portfolio_position_close_fields.py` ✓
- [x] `backend/tests/test_portfolio_close.py` ✓
- [x] `backend/app/models/portfolio_v2.py` (modified) ✓
- [x] `backend/app/api/portfolio_v2.py` (modified) ✓
- [x] `frontend/src/lib/api.ts` (modified) ✓
- [x] `frontend/src/app/portfolio/page.tsx` (modified) ✓
- [x] `frontend/src/app/portfolio/page.module.css` (modified) ✓

### Commits exist

- [x] 1b2e9d0 — chore(38-01): DB migration 004
- [x] 9e57220 — feat(38-01): backend PATCH + updated GET
- [x] 454c1b1 — test(38-01): backend tests
- [x] 5f2cfb4 — feat(38-01): frontend API
- [x] a5d5c30 — feat(38-01): frontend UI

### Verifications

- [x] `alembic current` → `004 (head)` ✓
- [x] PATCH route registered: `/portfolio/positions/{position_id}/close` ✓
- [x] 5/5 backend tests pass ✓
- [x] `npx tsc --noEmit` — 0 errors ✓

## Self-Check: PASSED
