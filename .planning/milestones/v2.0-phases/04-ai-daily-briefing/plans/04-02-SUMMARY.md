---
phase: 4
plan: 2
subsystem: briefing-generator
tags: [briefing, llm, scheduler, kap, notable-stocks, macro, upsert]
dependency_graph:
  requires: [04-01]
  provides: [briefing_generator.py, generate_daily_briefing, _upsert_briefing, DailyCommentary]
  affects: [04-03-scheduler-integration]
tech_stack:
  added: [zoneinfo (stdlib), sqlalchemy.dialects.postgresql.insert]
  patterns: [concurrent asyncio.gather with return_exceptions, ON CONFLICT DO UPDATE upsert, instructor reuse across services, per-stage exception isolation]
key_files:
  created:
    - backend/app/services/briefing_generator.py
  modified: []
key_decisions:
  - "_is_notable_stock uses strictly-greater comparisons (> 2x, > 3.0%) — boundary values are excluded by test spec"
  - "generate_daily_briefing isolates each pipeline stage in its own try/except — partial briefings (no LLM) are stored rather than aborted"
  - "_upsert_briefing uses postgresql_insert ON CONFLICT — created_at excluded from SET clause to preserve first-generation timestamp"
  - "_fetch_overnight_kap bypasses kap_parser.fetch_latest_announcements (which applies max_age_hours) — queries NewsItem directly to avoid silent 06:30 data loss"
  - "_compute_notable_stocks uses MAX(date) < today to gracefully handle market holidays"
  - "_generate_commentary reuses llm_sentiment_service._patched_client and _llm_semaphore — no duplicate client initialisation"
metrics:
  duration_minutes: 8
  completed_date: "2026-04-18"
  tasks_completed: 1
  files_created: 1
  files_modified: 0
---

# Phase 4 Plan 2: Briefing Generator Summary

**One-liner:** Morning briefing orchestrator collecting overnight KAP + notable stocks + macro, generating DailyCommentary via instructor/DeepSeek, and idempotently upserting to PostgreSQL with per-stage exception isolation.

## What Was Built

`backend/app/services/briefing_generator.py` — the core pipeline service for AI Daily Briefing.

### Functions implemented

| Function | Purpose |
|---|---|
| `_is_notable_stock` | Pure helper: volume > 2x avg OR abs(change_pct) > 3.0 (strictly greater) |
| `overnight_window` | Returns (start_utc, end_utc) — yesterday 18:00 Istanbul DST-safe |
| `_fetch_overnight_kap` | Queries NewsItem table directly for KAP items in overnight window |
| `_compute_notable_stocks` | Finds notable BIST stocks via MAX(date) + 28-day avg vol subquery |
| `_fetch_macro_snapshot` | Concurrent asyncio.gather on TCMB policy rate, FX reserves, press release |
| `_summarise_kap` | Formats KAP items to Turkish text block |
| `_summarise_notable_stocks` | Formats notable stocks to Turkish text block |
| `_summarise_macro` | Formats macro dict to compact Turkish text |
| `_generate_commentary` | Calls instructor via shared _patched_client + _llm_semaphore |
| `_upsert_briefing` | postgresql INSERT ... ON CONFLICT (date) DO UPDATE |
| `generate_daily_briefing` | Full orchestrator — called by APScheduler (04-03) |

### Models added

| Model | Fields |
|---|---|
| `DailyCommentary` | `risk_summary: str`, `opportunities: List[str]`, `watch_list: List[str]` |

## Test Results

Targeted tests:
- `test_notable_stocks_algorithm` — xpassed (was xfail)
- `test_daily_commentary_model` — xpassed (was xfail)
- `test_briefing_upsert` — xpassed (was xfail)

Full suite: **21 passed, 11 xpassed, 2 xfailed, 0 errors** — no regressions.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None. All functions are fully wired. `_fetch_macro_snapshot` depends on `tcmb_adapter` (pre-existing service) which may itself return partial data — this is handled via `return_exceptions=True` in `asyncio.gather` and graceful fallback in `_summarise_macro`.

## Self-Check: PASSED

- `/Users/nedimkopurlu/Downloads/PROJELER/stalize/backend/app/services/briefing_generator.py` — FOUND
- Commit `13c5575e` — FOUND (feat(04-02): implement briefing_generator.py)
- 3 targeted tests — xpassed
- Full suite — 0 failures, 0 errors
