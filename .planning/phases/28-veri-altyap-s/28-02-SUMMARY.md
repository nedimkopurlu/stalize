---
phase: 28-veri-altyap-s
plan: "02"
subsystem: backend/market-api
tags: [market, bist100, forex, gold, endpoints, tdd]
dependency_graph:
  requires: ["28-01"]
  provides: ["/market/bist100", "/market/forex", "/market/gold"]
  affects: ["29-dashboard"]
tech_stack:
  added: []
  patterns:
    - "CommodityPrice last-2-row pattern for daily change computation"
    - "Symbol-keyed in-memory dict cache (60s TTL) — mirrors macro.py"
    - "Dependency injection override (_override_db_with_rows_map) for deterministic unit tests"
    - "Local _latest_close_and_date helper avoids cross-router coupling with macro.py"
key_files:
  created: []
  modified:
    - backend/app/api/market.py
    - backend/tests/test_market_endpoints.py
decisions:
  - "Compute change_pct from last 2 CommodityPrice rows instead of reading change_pct column (Pitfall 6 — column often NULL)"
  - "Volume=0 masked to None for BIST100 index (Pitfall 1 — index volume unreliable)"
  - "_latest_close_and_date is a local helper rather than importing from macro.py — avoids cross-router coupling"
  - "FOREX pair with 0 DB rows silently skipped; pair with 1 row included with daily_change_pct=None"
  - "Gold formula: gram_try = gold_usd * usdtry / 31.1035; all coin forms = gram_try * GOLD_COIN_WEIGHTS[form]"
metrics:
  duration_minutes: 3
  tasks_completed: 3
  tasks_total: 3
  files_changed: 2
  completed_date: "2026-05-05T16:30:42Z"
---

# Phase 28 Plan 02: Market Endpoints (bist100, forex, gold) Summary

**One-liner:** Three market read endpoints (BIST100 index, 6 forex TRY pairs, 5 gold forms) backed by CommodityPrice table with computed daily change, 60s cache, and 503 guard on missing data.

## What Was Built

Three FastAPI endpoints appended to `backend/app/api/market.py`:

### GET /api/market/bist100

Reads latest 2 CommodityPrice rows for `XU100.IS`, computes `daily_change_pct` from the two closes, masks `volume=0` to `None`.

Example response:
```json
{
  "value": 10534.27,
  "daily_change_pct": 0.73,
  "volume": null,
  "as_of": "2026-05-05"
}
```

503 case: `{"detail": "BIST100 verisi yok"}` when no XU100.IS rows exist.

### GET /api/market/forex

Iterates `FOREX_PAIRS` dict (6 TRY pairs: USD, EUR, GBP, CNY, JPY, CHF). For each symbol reads latest 2 rows and computes `daily_change_pct`. Pairs with no DB rows are silently omitted; pairs with 1 row report `daily_change_pct: null`.

Example response:
```json
{
  "pairs": [
    {"symbol": "USDTRY=X", "name": "USD/TRY", "rate": 34.5, "daily_change_pct": 1.47, "as_of": "2026-05-05"},
    ...
  ],
  "count": 5,
  "as_of": "2026-05-05T16:28:00Z"
}
```

### GET /api/market/gold

Reads latest `GC=F` (gold USD/oz) and `USDTRY=X`, computes `gram_try = gold_usd * usdtry / 31.1035`, then multiplies by `GOLD_COIN_WEIGHTS` for each form.

Example response:
```json
{
  "forms": {
    "gram": 2624.07,
    "ons": 81668.10,
    "ceyrek": 4602.61,
    "yarim": 9205.22,
    "tam": 18420.43
  },
  "gold_usd_per_oz": 2400.00,
  "usdtry": 34.0,
  "as_of": "2026-05-05"
}
```

503 case: `{"detail": "Altın verisi yok"}` when either GC=F or USDTRY=X rows are missing.

## Cache TTL Behavior

All three endpoints use the module-level `_market_cache` dict (mirrors `macro.py` pattern). Each entry stores `{"ts": epoch_float, "data": response_dict}`. TTL = 60 seconds. Cache key per endpoint: `"bist100"`, `"forex"`, `"gold"`. Tests call `_market_cache.clear()` before each assertion to bypass cache.

## Helper

`_latest_close_and_date(db, symbol)` — local async helper that reads the single most recent CommodityPrice row for a symbol and returns `(close_float, iso_date_str)`. Intentionally not imported from `macro.py` to avoid cross-router coupling.

## Test Results

| Test | Result |
|------|--------|
| test_bist100_endpoint_returns_value_and_change | PASS |
| test_bist100_endpoint_single_row_returns_none_change | PASS |
| test_bist100_endpoint_no_data_returns_503 | PASS |
| test_forex_endpoint_returns_pairs_with_computed_change | PASS |
| test_forex_pairs_includes_jpy_chf | PASS |
| test_gold_endpoint_computes_all_five_forms | PASS |
| test_gold_endpoint_missing_data_returns_503 | PASS |
| test_gold_coin_weights_constants | PASS |
| test_market_router_mounted | PASS |
| test_opportunities_endpoint | xfail (Plan 28-03) |

Total: 9 passed, 1 xfailed, 0 failed

## Pitfalls Honored

- **Pitfall 1 (volume=0 → None):** BIST100 `volume_val` only set when `today.volume is not None and today.volume > 0`.
- **Pitfall 6 (compute change_pct, not read):** Both bist100 and forex compute `change_pct = (today.close - yesterday.close) / yesterday.close * 100` from the two row closes; the `CommodityPrice.change_pct` column is never accessed.

## Deviations from Plan

None — plan executed exactly as written. All three tasks were implemented together in a single TDD cycle (write all tests RED → implement all endpoints GREEN) since all three tasks modify the same two files.

## Known Stubs

None. All endpoints return live data from CommodityPrice table or 503 when data is absent.

## Self-Check: PASSED

- `backend/app/api/market.py` — FOUND: contains all 3 `@router.get` endpoints
- `backend/tests/test_market_endpoints.py` — FOUND: 9 tests pass
- Commit `b737c76` — verified (see git log)
