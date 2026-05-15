---
phase: 51
plan: "01"
subsystem: backend
tags: [sector-scoring, migration, tdd, api]
dependency_graph:
  requires: [Phase 48 data_quality_score, Phase 49 amihud_ratio, Phase 50 market_regime]
  provides: [sector_category, sector_score, sector_scoring_method, nav_discount on Stock]
  affects: [GET /stocks, GET /stocks/{symbol}, GET /stocks/{symbol}/score-breakdown, update_all_scores()]
tech_stack:
  added: []
  patterns: [idempotent Alembic migration, pure function sector classification, TDD red-green, sector score override of fundamental_score]
key_files:
  created:
    - backend/alembic/versions/011_add_sector_scoring_columns.py
    - backend/tests/test_sector_scoring.py
  modified:
    - backend/app/models/stock.py
    - backend/app/services/scoring.py
    - backend/app/api/stocks.py
decisions:
  - "classify_sector_category uses symbol-first lookup (BANK_TICKERS/HOLDING_TICKERS frozensets) then falls back to sector string 'real estate' match for GYO"
  - "Bank and GYO stocks have fundamental_score overridden by sector-specific formula; holding stocks get nav_discount adjustment on top of existing fundamental_score"
  - "Sector component in score-breakdown has base_weight=0.0 (informational only, does not affect overall_score calculation)"
  - "HOLDING_SUBSIDIARIES maps to known Borsa Istanbul symbols for NAV proxy computation"
metrics:
  duration: "~15 minutes"
  completed: "2026-05-15"
  tasks_completed: 3
  files_changed: 5
---

# Phase 51 Plan 01: Sector-Based Scoring Backend Summary

**One-liner:** Bank P/TBV+ROE and GYO P/B proxy scoring with holding NAV discount, all integrated into update_all_scores() and exposed via three API endpoints.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Migration 011 + Stock ORM columns | 5cb1f31 | 011_add_sector_scoring_columns.py, stock.py |
| 2 | Sector classification + scoring functions (TDD) | c4c2b4e | scoring.py, test_sector_scoring.py |
| 3 | API serialization — sector fields in list, detail, score-breakdown | 777428f | stocks.py |

## What Was Built

**Migration 011** (`backend/alembic/versions/011_add_sector_scoring_columns.py`):
- Idempotent inspector pattern; adds four nullable columns to `stocks` table: `sector_category VARCHAR(20)`, `sector_score FLOAT`, `sector_scoring_method VARCHAR(50)`, `nav_discount FLOAT`
- Applied: `010 -> 011` upgrade successful

**Stock ORM** (`backend/app/models/stock.py`):
- Four new SQLAlchemy columns appended after `amihud_ratio`

**Scoring Service** (`backend/app/services/scoring.py`):
- `BANK_TICKERS` (9 banks), `HOLDING_TICKERS` (5 holdings), `HOLDING_SUBSIDIARIES` constants
- `classify_sector_category(symbol, sector_str) -> Optional[str]`: symbol-first lookup, real estate fallback for GYO
- `_score_ptbv_tier(pb_ratio)` and `_score_roe_tier(roe)` shared private helpers
- `calculate_bank_score(pb_ratio, roe)`: 60% P/TBV + 40% ROE, overrides `fundamental_score`
- `calculate_gyo_score(pb_ratio)`: P/B as NAV proxy, overrides `fundamental_score`
- `calculate_holding_nav_discount(holding_market_cap, sub_sum)`: (sub_sum - holding_cap) / sub_sum
- `update_all_scores()` extended with sector scoring block after amihud computation

**API** (`backend/app/api/stocks.py`):
- `GET /stocks`: added `sector_category`, `sector_score`, `sector_scoring_method`, `nav_discount` per item
- `GET /stocks/{symbol}`: added same four fields in stock detail dict
- `GET /stocks/{symbol}/score-breakdown`: appends `sector_component` when `sector_scoring_method` is set; returns `sector_category`, `sector_scoring_method`, `nav_discount` in root response dict

## TDD Results

24 tests in `backend/tests/test_sector_scoring.py` — all pass.

Test coverage:
- 2 tests: bank ticker classification (all 9 symbols)
- 2 tests: holding ticker classification (all 5 symbols)
- 3 tests: GYO classification (real estate sector string, case insensitivity)
- 2 tests: unknown/None returns None
- 6 tests: `calculate_bank_score` boundary conditions including None inputs
- 5 tests: `calculate_gyo_score` tier boundaries
- 4 tests: `calculate_holding_nav_discount` (discount, premium, None guards)
- 2 tests: constant set contents verification

## Verification Results

```
classify_sector_category AKBNK: banka
classify_sector_category ISGYO: gyo
classify_sector_category SAHOL: holding
calculate_bank_score 0.7 0.22: 100.0
```

All success criteria met:
- Migration 011 at `backend/alembic/versions/011_add_sector_scoring_columns.py` with `revision="011"`, `down_revision="010"`
- Stock ORM has all four sector columns
- `classify_sector_category('AKBNK', ...)` == `"banka"`, `('ISGYO', 'Real Estate')` == `"gyo"`, `('SAHOL', ...)` == `"holding"`, `('THYAO', 'Industrials')` == `None`
- `calculate_bank_score(0.7, 0.22)` == `100.0`
- 24 tests pass
- `sector_category` and `nav_discount` in GET /stocks and GET /stocks/{symbol}
- `sector_score` component in score-breakdown when `sector_scoring_method` is set

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all sector classification and scoring functions are wired with real logic. Holding NAV discount depends on subsidiary stocks being present in the DB; if subsidiaries have no market_cap data, `nav_discount` will be `None` (documented expected behavior, not a stub).

## Self-Check: PASSED

Files verified:
- `backend/alembic/versions/011_add_sector_scoring_columns.py` — FOUND
- `backend/tests/test_sector_scoring.py` — FOUND (24 tests, all pass)
- `backend/app/models/stock.py` — sector_category column FOUND
- `backend/app/services/scoring.py` — classify_sector_category FOUND
- `backend/app/api/stocks.py` — sector_score FOUND

Commits verified:
- `5cb1f31` — feat(51-01): migration 011 + Stock ORM sector scoring columns
- `c4c2b4e` — feat(51-01): sector classification + scoring functions with TDD tests
- `777428f` — feat(51-01): expose sector fields in stocks list, detail, and score-breakdown API
