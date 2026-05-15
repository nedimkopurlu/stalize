---
phase: 50-market-regime-engine
plan: "01"
subsystem: backend
tags: [market-regime, alembic, apscheduler, tdd, ema200, adx, atr]
dependency_graph:
  requires: []
  provides: [market_regime_table, GET /api/market-regime, MarketRegimeEngine]
  affects: [frontend-plan-50-02]
tech_stack:
  added: []
  patterns: [tdd-red-green, delete-then-insert-upsert, cron-scheduler-job]
key_files:
  created:
    - backend/alembic/versions/010_add_market_regime_table.py
    - backend/app/models/market_regime.py
    - backend/app/services/market_regime.py
    - backend/tests/test_market_regime.py
  modified:
    - backend/app/models/__init__.py
    - backend/app/api/market.py
    - backend/app/main.py
decisions:
  - "Volatil takes highest priority in _classify_regime (ATR/close >= 2% overrides all other conditions)"
  - "No cold-start trigger for market regime job — previous day's DB row is sufficient until next 18:30"
  - "detect_regime is sync; update_regime is async — allows pure unit testing without mocking DB"
metrics:
  duration: "~15 minutes"
  completed: "2026-05-15"
  tasks_completed: 3
  files_changed: 7
---

# Phase 50 Plan 01: Market Regime Engine Summary

**One-liner:** Daily BIST100 regime detection (Boğa/Ayı/Yatay/Volatil) via USD-adjusted XU100.IS + ADX/EMA200/ATR, persisted to `market_regime` table and served via `GET /api/market-regime`.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Migration 010 + MarketRegime ORM | `04854a4` | `010_add_market_regime_table.py`, `models/market_regime.py`, `models/__init__.py` |
| 2 (RED) | Failing tests for _classify_regime | `04dde75` | `tests/test_market_regime.py` |
| 2 (GREEN) | MarketRegimeEngine service | `30879f6` | `services/market_regime.py` |
| 3 | API endpoint + APScheduler job | `46f0809` | `api/market.py`, `main.py` |

## Artifacts

- **Migration:** `backend/alembic/versions/010_add_market_regime_table.py` — `revision="010"`, idempotent `inspector.get_table_names()` check, all 6 columns (id, date UNIQUE, regime, adx, ema200, atr, created_at). Applied successfully.
- **ORM Model:** `backend/app/models/market_regime.py` — `class MarketRegime(Base)`, `__tablename__="market_regime"`.
- **Service:** `backend/app/services/market_regime.py` — `_classify_regime()` pure method, `detect_regime()` sync yfinance fetcher, `update_regime()` async DB upsert, `market_regime_engine` singleton.
- **Endpoint:** `GET /api/market-regime` in `backend/app/api/market.py` — returns `{regime, date, adx, ema200, atr}` or 404 if no data.
- **Scheduler:** `background_market_regime_update` registered in lifespan at `cron(day_of_week="mon-fri", hour=18, minute=30, timezone="Europe/Istanbul")`.

## Test Results

```
6 passed, 2 warnings in 0.78s
tests/test_market_regime.py::test_classify_boga PASSED
tests/test_market_regime.py::test_classify_ayi PASSED
tests/test_market_regime.py::test_classify_yatay PASSED
tests/test_market_regime.py::test_classify_volatil_overrides_boga PASSED
tests/test_market_regime.py::test_classify_volatil_overrides_ayi PASSED
tests/test_market_regime.py::test_classify_volatil_with_weak_adx PASSED
```

## Regime Classification Logic

Priority order (highest to lowest):
1. **Volatil** — `atr / usd_close >= 0.02` (overrides all)
2. **Ayı** — `usd_close < ema200 AND adx > 25`
3. **Boğa** — `usd_close > ema200 AND adx > 25`
4. **Yatay** — default (weak ADX or neutral positioning)

## Decisions Made

1. Volatil takes highest priority — high volatility is a market state independent of trend direction, so it overrides Bull/Bear classification.
2. No startup trigger for the cron job — regime detection requires 210+ days of data and is only valid post-market-close; on cold start any prior DB row is good enough.
3. `detect_regime()` is synchronous (blocking yfinance call) while `update_regime()` is async — this separation allows pure unit testing of `_classify_regime()` without any mocking.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all data paths are wired. `GET /api/market-regime` returns 404 until first cron job runs or `update_regime()` is called manually.

## Self-Check: PASSED

- `backend/alembic/versions/010_add_market_regime_table.py` exists: FOUND
- `backend/app/models/market_regime.py` exists: FOUND
- `backend/app/services/market_regime.py` exists: FOUND
- `backend/tests/test_market_regime.py` exists: FOUND
- `backend/app/api/market.py` contains "/market-regime": FOUND
- `backend/app/main.py` contains "background_market_regime_update": FOUND
- Commits 04854a4, 04dde75, 30879f6, 46f0809: all present in git log
- All 6 pytest tests: PASSED
