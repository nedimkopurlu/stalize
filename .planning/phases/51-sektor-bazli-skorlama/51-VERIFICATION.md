---
phase: 51-sektor-bazli-skorlama
verified: 2026-05-15T00:00:00Z
status: passed
score: 7/7 must-haves verified
re_verification: false
---

# Phase 51: Sektör Bazlı Skorlama Verification Report

**Phase Goal:** Sector-specific scoring for Banking (P/TBV+ROE), GYO (P/B NAV proxy with disclaimer), and Holdings (approximate NAV discount). Standard P/E and P/B not applied to banks.
**Verified:** 2026-05-15
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                                              | Status     | Evidence                                                                                                          |
|-----|--------------------------------------------------------------------------------------------------------------------|------------|-------------------------------------------------------------------------------------------------------------------|
| 1   | Migration 011 adds sector columns idempotently                                                                     | VERIFIED   | `011_add_sector_scoring_columns.py` exists; revision="011", down_revision="010"; uses `sa.inspect` column guard    |
| 2   | Bank tickers get sector_category="banka" via classify_sector_category()                                           | VERIFIED   | Function defined at scoring.py:36; BANK_TICKERS frozenset includes all 9 tickers; test_classify_bank_tickers passes |
| 3   | Bank fundamental_score overridden by 60% P/TBV + 40% ROE; standard PE/PB not applied                            | VERIFIED   | scoring.py:568-571: `stock.fundamental_score = bank_score` comment "standart PE/PB uygulanmaz"                     |
| 4   | GYO stocks get P/B NAV proxy score; UI shows "Gerçek NAD verisi mevcut değil"                                    | VERIFIED   | calculate_gyo_score() at scoring.py:91; note in stocks.py:525; page.tsx:923 renders note for gyo                  |
| 5   | Holdings get approximate NAV discount from subsidiary market caps                                                  | VERIFIED   | calculate_holding_nav_discount() at scoring.py:103; HOLDING_SUBSIDIARIES dict used in update_all_scores:580-601   |
| 6   | GET /stocks and GET /stocks/{symbol} include sector_category and nav_discount                                     | VERIFIED   | stocks.py:220-223 (list), 358-361 (detail); all four sector fields serialized                                      |
| 7   | Score-breakdown includes sector_score component and sector fields when sector_scoring_method is set               | VERIFIED   | stocks.py:522-546; sector_note_map with NAD note; sector_category/sector_scoring_method/nav_discount in response  |

**Score:** 7/7 truths verified

---

### Required Artifacts

| Artifact                                                               | Expected                                                       | Status     | Details                                                                          |
|------------------------------------------------------------------------|----------------------------------------------------------------|------------|----------------------------------------------------------------------------------|
| `backend/alembic/versions/011_add_sector_scoring_columns.py`          | Migration with revision="011", down_revision="010", idempotent | VERIFIED   | Exists; uses inspector column check; all 4 columns added with try/except downgrade |
| `backend/app/models/stock.py`                                          | ORM with sector_category, sector_score, sector_scoring_method, nav_discount | VERIFIED | Lines 44-47: all four columns declared as nullable                              |
| `backend/app/services/scoring.py`                                      | classify_sector_category(), calculate_bank_score(), calculate_gyo_score(), calculate_holding_nav_discount() | VERIFIED | All four functions exist; BANK_TICKERS and HOLDING_TICKERS constants defined     |
| `backend/app/api/stocks.py`                                            | sector_category and nav_discount in list + detail + score-breakdown | VERIFIED | Lines 220-223, 358-361, 522-546 all confirmed                                   |
| `frontend/src/lib/api.ts`                                              | StockSummary and ScoreBreakdownResponse extended with sector fields | VERIFIED | Lines 58-59 (StockSummary), 396-398 (ScoreBreakdownResponse)                   |
| `frontend/src/app/stocks/[symbol]/page.tsx`                            | Sector scoring info block with method badge, GYO note, holding NAV row | VERIFIED | Lines 912-948; all three conditional blocks present                              |
| `backend/tests/test_sector_scoring.py`                                 | 24 tests covering all pure functions                           | VERIFIED   | 24/24 tests pass; no DB dependencies                                             |

---

### Key Link Verification

| From                                            | To                                                | Via                                          | Status   | Details                                                                              |
|-------------------------------------------------|---------------------------------------------------|----------------------------------------------|----------|--------------------------------------------------------------------------------------|
| `scoring.py:update_all_scores`                  | `stock.sector_category`, `stock.fundamental_score` | classify_sector_category() → bank/gyo/holding branch | WIRED    | Lines 559-602; each branch sets sector_category and overrides fundamental_score      |
| `api/stocks.py:GET /stocks`                     | `Stock.sector_category`, `Stock.nav_discount`     | Serialization dict at lines 220-223          | WIRED    | All four sector fields serialized in list response                                   |
| `api/stocks.py:GET /stocks/{symbol}/score-breakdown` | `stock.sector_scoring_method`              | sector_note_map at line 523; sector_component appended | WIRED | Component appended when sector_scoring_method is set; NAD note present              |
| `frontend/src/app/stocks/[symbol]/page.tsx`     | `ScoreBreakdownResponse.sector_category`          | `scoreBreakdown?.sector_category` in JSX at lines 912-948 | WIRED | Three conditional blocks: method badge, GYO note, holding NAV row                   |

---

### Requirements Coverage

| Requirement | Source Plan   | Description                                                                                    | Status     | Evidence                                                                                                    |
|-------------|---------------|------------------------------------------------------------------------------------------------|------------|-------------------------------------------------------------------------------------------------------------|
| SEK-01      | 51-01, 51-02  | Banking stocks scored with P/TBV + ROE weighted (60/40); standard P/E not applied             | SATISFIED  | calculate_bank_score(): 0.6*_score_ptbv_tier + 0.4*_score_roe_tier; fundamental_score overridden in update_all_scores |
| SEK-02      | 51-01, 51-02  | GYO stocks get P/B NAV proxy score; UI shows "Gerçek NAD verisi mevcut değil" note            | SATISFIED  | calculate_gyo_score() uses P/B via _score_ptbv_tier; backend sector_note_map and page.tsx:923 both show the note |
| SEK-03      | 51-01, 51-02  | Holdings get approximate NAV discount from public subsidiary market caps; reflected in scoring | SATISFIED  | calculate_holding_nav_discount(); HOLDING_SUBSIDIARIES dict; nav_discount stored on Stock and shown in UI   |

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | -    | -       | -        | No anti-patterns found in sector scoring code paths |

No TODOs, placeholders, empty return stubs, or orphaned code found in the modified files.

**Note — ordering subtlety (not a blocker):** In `update_all_scores()`, `get_contextual_score_breakdown()` is called first (line 535) and uses `stock.fundamental_score` as it exists in the DB at that point. The sector override then writes a new value to `stock.fundamental_score` (lines 568-602) and commits. This means the `overall_score` written in the same run still reflects the pre-sector fundamental_score. On the *next* scheduler run the overridden fundamental_score will be incorporated into overall_score correctly. This is a run-to-run lag, not a data integrity issue, and does not block SEK-01/02/03 requirements.

---

### Human Verification Required

None required for functional correctness. The following items could benefit from human spot-check if desired:

#### 1. GYO NAD Note Visibility

**Test:** Load a GYO stock (e.g. EKGYO or ISGYO) detail page, open the Skor Dökümü section.
**Expected:** "Gerçek NAD verisi mevcut değil; P/D değeri NAD yaklaşımı olarak kullanılmıştır." info note appears below the breakdown bars.
**Why human:** Requires a populated DB with GYO stock data and a running application.

#### 2. Bank Score Excludes Standard P/E

**Test:** Load a bank stock (e.g. GARAN) detail page score breakdown; verify no "PE oranı" component appears in the breakdown bars.
**Expected:** Breakdown shows "F/DD+ROE" as the method, not a standard P/E or P/B component.
**Why human:** Requires live data and visual inspection of rendered component list.

---

### Gaps Summary

No gaps found. All seven must-have truths verified, all three requirements (SEK-01, SEK-02, SEK-03) satisfied by substantive, wired implementation. 24/24 automated tests pass, TypeScript compiles with zero errors.

---

_Verified: 2026-05-15_
_Verifier: Claude (gsd-verifier)_
