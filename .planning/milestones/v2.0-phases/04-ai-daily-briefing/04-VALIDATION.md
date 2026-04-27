# Phase 4: AI Daily Briefing — Validation Strategy

**Phase:** 04-ai-daily-briefing
**Requirements in scope:** BREF-01, BREF-02, BREF-03, BREF-04, BREF-05
**Created:** 2026-04-17

---

## Test File

`backend/tests/test_daily_briefing.py`

Run command:
```
cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && \
  /Applications/Xcode.app/Contents/Developer/usr/bin/python3 \
  -m pytest tests/test_daily_briefing.py -x -q
```

Full suite regression:
```
cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && \
  /Applications/Xcode.app/Contents/Developer/usr/bin/python3 \
  -m pytest tests/ -q
```

---

## Requirement → Test Map

| Req ID | Behavior | Test Name | Wave | Automated |
|--------|----------|-----------|------|-----------|
| BREF-02 | DailyBriefing ORM has all 9 required columns | `test_daily_briefing_model_fields` | 1 | yes |
| BREF-02 | GET /api/briefing/today → 404 when no record | `test_briefing_today_endpoint_404` | 1 | yes |
| BREF-02 | GET /api/briefing/today → 200 + X-Cache: HIT | `test_briefing_today_endpoint_200` | 1 | yes |
| BREF-04 | volume > 2× avg OR abs(change) > 3% flagged | `test_notable_stocks_algorithm` | 2 | yes |
| BREF-05 | DailyCommentary validates risk_summary, opportunities, watch_list | `test_daily_commentary_model` | 2 | yes |
| BREF-02 | _upsert_briefing idempotent (ON CONFLICT DO UPDATE) | `test_briefing_upsert` | 2 | yes |
| BREF-01 | APScheduler job named generate_daily_briefing at Europe/Istanbul | `test_briefing_cron_registered` | 3 | yes |

---

## Wave Gate Criteria

### Wave 0 Gate (before Wave 1 starts)
- [ ] `pytest tests/test_daily_briefing.py --collect-only` shows 7 tests, zero collection errors
- [ ] `pytest tests/test_daily_briefing.py` reports `7 xfailed` (no ERROR, no FAILED)

### Wave 1 Gate (before Wave 2 starts)
- [ ] `test_daily_briefing_model_fields` → xpass
- [ ] `test_briefing_today_endpoint_404` → xpass
- [ ] `test_briefing_today_endpoint_200` → xpass
- [ ] No regression in existing test suite

### Wave 2 Gate (before Wave 3 starts)
- [ ] `test_notable_stocks_algorithm` → xpass
- [ ] `test_daily_commentary_model` → xpass
- [ ] `test_briefing_upsert` → xpass
- [ ] No regression in existing test suite

### Wave 3 Gate (Phase complete)
- [ ] `test_briefing_cron_registered` → xpass
- [ ] All 7 stubs xpass
- [ ] `pytest tests/ -q` — full suite green
- [ ] Human checkpoint approved (see 04-03-scheduler-integration.md)

---

## Acceptance Criteria (Goal-Backward)

### Observable Truths (user perspective)

1. `GET /api/briefing/today` responds in <100ms with today's briefing when the cron has run
2. `GET /api/briefing/today` returns 404 `{"detail": "Brifing henüz üretilmedi"}` before the cron runs
3. The cron fires automatically at 06:30 Europe/Istanbul every weekday — no manual trigger needed
4. If re-triggered on the same day, the endpoint shows updated data (upsert, not duplicate)
5. If the DeepSeek LLM is unavailable, a partial briefing (without ai_commentary) is still stored

### Required Artifacts

| File | Purpose |
|------|---------|
| `backend/app/models/model_daily_briefing.py` | DailyBriefing ORM — daily_briefings table with unique constraint on date |
| `backend/app/models/__init__.py` | Imports DailyBriefing so Base.metadata.create_all discovers the table |
| `backend/app/api/briefing.py` | GET /briefing/today endpoint — DB lookup only, no LLM at request time |
| `backend/app/services/briefing_generator.py` | Core pipeline: KAP query, notable stocks, TCMB macro, LLM commentary, PostgreSQL upsert |
| `backend/app/main.py` | APScheduler cron: generate_daily_briefing, mon-fri, 06:30, timezone=Europe/Istanbul |
| `backend/tests/test_daily_briefing.py` | 7 xfail stubs → all xpass after Wave 3 |

### Key Links (critical wiring)

| From | To | Via | Breakage Symptom |
|------|----|-----|-----------------|
| `main.py` scheduler | `briefing_generator.generate_daily_briefing` | APScheduler cron job | No briefing ever generated |
| `briefing_generator._fetch_overnight_kap` | `news_items` table | `select(NewsItem).where(source='KAP', published_at >= start_utc)` | Empty KAP section in briefing |
| `briefing_generator._upsert_briefing` | `daily_briefings` table | `postgresql_insert().on_conflict_do_update(index_elements=['date'])` | Duplicate rows on rerun |
| `api/briefing.py` | `daily_briefings` table | `select(DailyBriefing).where(date == today)` | 404 even when briefing exists |
| `briefing_generator._generate_commentary` | DeepSeek via instructor | `llm_sentiment_service._patched_client` with `response_model=DailyCommentary` | ai_commentary always None |

---

## Pitfall Guard

These issues were flagged in RESEARCH.md and must be verified during execution:

| Pitfall | Check |
|---------|-------|
| Missing `timezone=` on cron job | `test_briefing_cron_registered` confirms `"Istanbul" in str(trigger.timezone)` |
| `briefing.py` router not imported in `main.py` | Wave 1 endpoint tests fail if import missing |
| `on_conflict_do_update` requires actual unique index | Created automatically by `UniqueConstraint` + `create_all` at startup |
| Naive datetime in overnight window query | `overnight_window()` returns tz-aware UTC datetimes |
| Notable stocks using yesterday's date (may be holiday) | `_compute_notable_stocks` queries `MAX(PriceHistory.date) WHERE date < today` |
| `ai_commentary = None` stored without error | `ai_commentary = Column(JSON, nullable=True)` |
| APScheduler jobs accessed outside FastAPI lifecycle | `AsyncSessionLocal()` used directly (not `get_db()` Depends) |

---

## Deferred (Out of Scope for Phase 4)

- Push notification when briefing is ready (v2)
- Manual regeneration endpoint `POST /api/briefing/generate` (v2)
- Multi-day briefing history `GET /api/briefing/history` (v2)
- UI: Dashboard morning briefing card (Phase 5 — UIUX-01)
