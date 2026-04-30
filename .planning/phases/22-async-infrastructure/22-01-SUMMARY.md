---
plan: 22-01
phase: 22-async-infrastructure
status: complete
requirements_satisfied:
  - ASYNC-01
  - ASYNC-02
---

# Plan 22-01 Summary: Sleep Fix + Session Migration

## What Was Done

**ASYNC-01 — time.sleep() cleanup:**
- `data_collector.py`: Added `import time` at module level; removed inline `import time` from inside `_fetch()`. The `time.sleep()` in `_fetch()` remains — it runs inside a `run_in_executor` thread so it does not block the event loop.
- `macro_news.py`: No changes needed. `time.sleep()` in `_fetch_single_ticker_news()` is a sync method called via `concurrent.futures.ThreadPoolExecutor` — it runs in a thread, not the event loop.

**ASYNC-02 — AsyncSessionLocal → Depends(get_db) migration:**

Migrated all API route handlers across 4 files:

| File | Handlers migrated |
|------|------------------|
| `stocks.py` | 11 (`get_stocks`, `get_stock_sectors`, `get_kap_feed`, `get_stock_detail`, `get_stock_prices`, `get_stock_score_breakdown`, `get_stock_news`, `get_stock_fundamentals`, `get_stock_peers`, `get_sectors`, `screen_stocks`) |
| `portfolio_v2.py` | 5 (`get_positions`, `get_history`, `add_position`, `close_position`, `add_change_log`) |
| `macro.py` | 1 (`get_macro_events`; helper functions `_latest_macro_reading` and `_latest_market_reading` kept as-is — service-level, not route handlers) |
| `admin.py` | 2 (`health_check`, `get_dashboard`) |

Pattern applied: `async with AsyncSessionLocal() as db:` removed; `db: AsyncSession = Depends(get_db)` added as last parameter; body dedented.

## Verification Results

```
ASYNC-02: No AsyncSessionLocal in route files → PASS (zero matches)
Depends(get_db) counts: stocks.py=11, portfolio_v2.py=5, macro.py=1, admin.py=2
ASYNC-01: time.sleep only in executor-bound sync functions
ASYNC-03/04: N/A (handled in 22-02)
App import: python3 -c "from app.main import app" → OK
```
