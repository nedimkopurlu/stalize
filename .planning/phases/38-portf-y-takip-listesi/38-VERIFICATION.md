---
phase: 38-portf-y-takip-listesi
verified: 2026-05-08T00:00:00Z
status: passed
score: 6/6 must-haves verified
re_verification: false
---

# Phase 38: Portföy Takip Listesi Verification Report

**Requirement:** PORT-02 — User enters a sell (close position) operation; closed position shows realized P&L in TL and %
**Verified:** 2026-05-08
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | DB schema has exit_price, exit_date, realized_pnl columns | VERIFIED | `004_portfolio_position_close_fields.py` adds all three columns via Alembic migration |
| 2 | PortfolioPosition ORM model carries close fields | VERIFIED | `portfolio_v2.py` lines 25-27: `exit_price`, `exit_date`, `realized_pnl` columns defined with correct types |
| 3 | GET /portfolio/positions returns both open and recently-closed (30 days) | VERIFIED | `portfolio_v2.py` lines 99-145: OR query `is_active=True OR (is_active=False AND exit_date >= cutoff)` with all fields in response dict |
| 4 | PATCH /portfolio/positions/{id}/close endpoint exists, calculates P&L, and persists | VERIFIED | `portfolio_v2.py` lines 302-350: endpoint validates exit_price > 0, computes `round((exit_price - entry_price) * quantity, 4)`, sets `is_active=False`, writes to DB |
| 5 | Frontend PortfolioPosition interface and closePosition() API method exist | VERIFIED | `api.ts` lines 297-314 (interface with is_active, exit_price, exit_date, realized_pnl), lines 766-770 (closePosition PATCH method) |
| 6 | Portfolio page renders "Kapat" button, inline close form, and "Geçmiş Pozisyonlar" section | VERIFIED | `page.tsx` lines 605-650 ("Kapat" button + inline form with exit_price/exit_date inputs + Onayla/İptal), lines 660-714 (Geçmiş Pozisyonlar table with realized P&L in TL and %) |

**Score:** 6/6 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/alembic/versions/004_portfolio_position_close_fields.py` | Migration with exit_price, exit_date, realized_pnl | VERIFIED | All 3 columns present; down_revision=003 correct |
| `backend/app/models/portfolio_v2.py` | PortfolioPosition with close fields | VERIFIED | Columns at lines 25-27 with correct nullable=True types |
| `backend/app/api/portfolio_v2.py` | GET positions (open+closed) + PATCH close endpoint | VERIFIED | GET returns both at line 92; PATCH at line 302; P&L formula at line 325 |
| `backend/tests/test_portfolio_close.py` | 5 tests covering success, P&L math, 404, 401, 422 | VERIFIED | All 5 tests pass (2.01s, 5 passed, 6 warnings) |
| `frontend/src/lib/api.ts` | PortfolioPosition interface with close fields; closePosition() | VERIFIED | Interface lines 297-314; method lines 766-770 |
| `frontend/src/app/portfolio/page.tsx` | Kapat button, inline form, Geçmiş Pozisyonlar section | VERIFIED | Lines 605-714; realized_pnl rendered in TL (formatTRY) and % (formatPct) |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| portfolio/page.tsx | api.closePosition() | handleClosePosition (line 329) | WIRED | Called with closingId and closeForm values; response triggers fetchPositions() refresh |
| closePosition() in api.ts | PATCH /portfolio/positions/{id}/close | apiFetch with method PATCH | WIRED | Lines 766-770; correct URL pattern and body shape |
| PATCH endpoint | PortfolioPosition ORM | SQLAlchemy select + field assignment | WIRED | Lines 315-331; pos.is_active, pos.exit_price, pos.exit_date, pos.realized_pnl all written then committed |
| GET /portfolio/positions | closed positions | OR query with 30-day cutoff | WIRED | Lines 99-109; closed positions included in response with exit_price, exit_date, realized_pnl |
| Geçmiş Pozisyonlar section | realized_pnl display | closedPositions filter + formatTRY/formatPct | WIRED | Lines 324-326 split; lines 699-706 render realized_pnl in TL and % |

---

## Requirements Coverage

| Requirement | Description | Status | Evidence |
|-------------|-------------|--------|---------|
| PORT-02 | User enters sell/close; closed position shows realized P&L in TL and % | SATISFIED | End-to-end: "Kapat" button → inline form → PATCH API → `realized_pnl = (exit_price - entry_price) * quantity` → Geçmiş Pozisyonlar table shows TL (formatTRY) and % column |

---

## Test Results

```
5 passed, 6 warnings in 2.01s
```

| Test | Result |
|------|--------|
| test_close_position_success | PASS — 200, id/symbol/status/realized_pnl in response |
| test_close_position_realized_pnl_calculation | PASS — round((50.75-45.3)*100, 4) verified |
| test_close_position_not_found | PASS — 404, "bulunamadı" in detail |
| test_close_position_wrong_api_key | PASS — 401 with wrong API key |
| test_close_position_invalid_price_zero | PASS — 422 for exit_price=0 |

**TypeScript check:** `npx tsc --noEmit` — zero errors, zero output.

---

## Anti-Patterns Found

None blocking. The `handleClosePosition` function has a `console.error` on failure (line 342) which is informational only and does not affect functionality.

---

## Human Verification Required

### 1. Inline Close Form UX

**Test:** Open portfolio page with at least one active position. Click "Kapat". Enter exit price and date. Click "Onayla".
**Expected:** Position disappears from "Pozisyonlarım" table and appears in "Geçmiş Pozisyonlar" with correct realized P&L in TL and %.
**Why human:** UI rendering and DOM state changes cannot be verified programmatically.

### 2. Realized P&L Sign Direction

**Test:** Close a position at a price lower than entry price.
**Expected:** Realized P&L shows negative value (red styling via `pnlNegative` class).
**Why human:** Visual color application depends on CSS class resolution in browser.

---

## Gaps Summary

No gaps. All six must-haves are fully implemented, wired, and test-verified. PORT-02 is satisfied.

---

_Verified: 2026-05-08T00:00:00Z_
_Verifier: Claude (gsd-verifier)_
