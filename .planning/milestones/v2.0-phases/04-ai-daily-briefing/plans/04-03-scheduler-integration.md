---
phase: 04-ai-daily-briefing
plan_id: "04-03"
title: "Wave 3 — APScheduler cron registration + full integration"
requirement: BREF-01
wave: 3
estimated_minutes: 25
type: execute
depends_on: ["04-02"]
files_modified:
  - backend/app/main.py
autonomous: true
must_haves:
  truths:
    - "APScheduler has a job for generate_daily_briefing at 06:30 Europe/Istanbul weekdays"
    - "Cron job uses timezone='Europe/Istanbul' explicitly (not OS timezone)"
    - "All 7 Wave-0 stubs now xpass — full BREF-01..BREF-05 acceptance"
    - "The full pytest suite is green with no regressions"
  artifacts:
    - path: "backend/app/main.py"
      provides: "APScheduler cron job for generate_daily_briefing"
      contains: "timezone.*Europe/Istanbul"
  key_links:
    - from: "backend/app/main.py"
      to: "backend/app/services/briefing_generator.py"
      via: "from app.services.briefing_generator import generate_daily_briefing"
    - from: "scheduler.add_job(...)"
      to: "generate_daily_briefing"
      via: "cron trigger, day_of_week='mon-fri', hour=6, minute=30, timezone='Europe/Istanbul'"
---

<objective>
Register the `generate_daily_briefing` cron job in `main.py` using APScheduler with an explicit `timezone="Europe/Istanbul"` argument. This is the final wiring that makes all five BREF requirements operational end-to-end.

Purpose: Completes Phase 4 — the pipeline runs automatically every weekday at 06:30 Istanbul time.
Output: One modified file (`backend/app/main.py`) — a background function import + one `scheduler.add_job` call.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/04-ai-daily-briefing/04-CONTEXT.md
@.planning/phases/04-ai-daily-briefing/RESEARCH.md
@backend/app/main.py
@.planning/phases/04-ai-daily-briefing/plans/04-01-SUMMARY.md
@.planning/phases/04-ai-daily-briefing/plans/04-02-SUMMARY.md

<interfaces>
<!-- What exists in main.py that this task builds on. -->

Existing APScheduler cron pattern (from main.py — exactly how TUIK and audit jobs are registered):
```python
# TUIK weekday cron — NO timezone arg (uses OS default — a known pitfall for this project)
scheduler.add_job(background_tuik_scan, "cron", day_of_week="mon-fri", hour=9, minute=0)

# Audit weekday cron — same pattern
scheduler.add_job(background_audit_and_learn, "cron", day_of_week="mon-fri", hour=18, minute=5)
```

BREF-01 correct registration (per RESEARCH.md — must include timezone= unlike existing jobs):
```python
scheduler.add_job(
    generate_daily_briefing,
    "cron",
    day_of_week="mon-fri",
    hour=6,
    minute=30,
    timezone="Europe/Istanbul",   # REQUIRED — existing jobs omit this, BREF-01 must not
)
```

Existing background function pattern (lazy import inside function body):
```python
async def background_tuik_scan():
    from app.services.tuik_adapter import run_tuik_scan   # lazy import
    ...
```

Module-level import pattern (also present for some functions — either pattern works):
```python
from app.api import stocks, macro, portfolio, intelligence, causal, admin, briefing
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Register generate_daily_briefing cron job in main.py</name>
  <files>backend/app/main.py</files>
  <action>
Make exactly two changes to `backend/app/main.py`. Do not touch any other part of the file.

**Change 1: Add background wrapper function** — insert after the existing `background_xgb_retrain` function definition (before the `@asynccontextmanager` decorator):

```python
async def background_daily_briefing():
    """Günlük sabah brifing üretimi (BREF-01) — Hafta içi 06:30 Europe/Istanbul."""
    from app.services.briefing_generator import generate_daily_briefing
    logging.info("TETİKLENDİ: Günlük sabah brifing üretimi (06:30 Istanbul)")
    try:
        await generate_daily_briefing()
    except Exception as e:
        logging.error(f"Günlük Brifing Üretim Hatası: {e}")
```

The lazy import (`from app.services.briefing_generator import generate_daily_briefing` inside the function body) follows the existing pattern used by `background_macro_scan`, `background_kap_scan`, etc. and avoids circular import issues at startup.

**Change 2: Register the cron job** — insert inside the `lifespan` async context manager, after the `scheduler.add_job(background_xgb_retrain, ...)` line and before `scheduler.start()`:

```python
    # Günlük Sabah Brifing Üretimi (06:30 Istanbul) — BREF-01
    # NOTE: timezone="Europe/Istanbul" is REQUIRED here. Unlike other cron jobs in this
    # file, the briefing must fire at local Istanbul time regardless of server OS timezone.
    scheduler.add_job(
        background_daily_briefing,
        "cron",
        day_of_week="mon-fri",
        hour=6,
        minute=30,
        timezone="Europe/Istanbul",
    )
```

Also update the logging.info message after scheduler.start() to include the new job. Change:
```
"(KAP: {settings.KAP_SCAN_INTERVAL_MIN}dk, TCMB: 2h, TUIK: 9:00, Fusion: 1h, Audit: 18:05, Portfolio: 18:15)."
```
to:
```
"(KAP: {settings.KAP_SCAN_INTERVAL_MIN}dk, TCMB: 2h, TUIK: 9:00, Fusion: 1h, Audit: 18:05, Portfolio: 18:15, Brifing: 06:30)."
```

IMPORTANT: The test `test_briefing_cron_registered` introspects `scheduler.get_jobs()` and checks for a job whose `func.__name__` is `"generate_daily_briefing"`. Since we're wrapping `generate_daily_briefing` inside `background_daily_briefing`, the registered func name will be `"background_daily_briefing"`, NOT `"generate_daily_briefing"`.

To make the test pass, register `generate_daily_briefing` directly (not via wrapper) OR import at module level. Use direct registration:

```python
# At module level (top of file), add import BEFORE lifespan definition:
# Do NOT lazy-import generate_daily_briefing — register the actual function for testability.
```

Revise the approach: instead of the wrapper function, do a module-level import and register directly. This is cleaner and makes `test_briefing_cron_registered` pass without any stub changes:

```python
# Near the top of main.py, with the other imports:
from app.services.briefing_generator import generate_daily_briefing
```

Then in the lifespan scheduler section:
```python
    # Günlük Sabah Brifing Üretimi (06:30 Istanbul) — BREF-01
    scheduler.add_job(
        generate_daily_briefing,
        "cron",
        day_of_week="mon-fri",
        hour=6,
        minute=30,
        timezone="Europe/Istanbul",
    )
```

This registers the actual `generate_daily_briefing` function object, so `job.func.__name__ == "generate_daily_briefing"` evaluates to True in the test.

Note on potential circular imports: `briefing_generator.py` imports from `app.models`, `app.core.database`, and `app.services.llm_sentiment`. None of these import from `app.main`, so the import is safe at module level.

Verify by reading the existing imports in main.py and confirming no circular path exists before making the module-level import change.
  </action>
  <verify>
    <automated>cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/test_daily_briefing.py::test_briefing_cron_registered -x -q</automated>
  </verify>
  <done>
    - `main.py` imports `generate_daily_briefing` from `app.services.briefing_generator`
    - `scheduler.add_job(generate_daily_briefing, "cron", day_of_week="mon-fri", hour=6, minute=30, timezone="Europe/Istanbul")` is present in lifespan
    - `test_briefing_cron_registered` xpasses (finds job, confirms Europe/Istanbul timezone)
    - Application starts cleanly (no import errors): `python -c "from app.main import app"` exits 0
  </done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>
    Complete Phase 4 pipeline:
    - Wave 0: 8 xfail test stubs in test_daily_briefing.py
    - Wave 1: DailyBriefing ORM model + GET /api/briefing/today endpoint
    - Wave 2: briefing_generator.py (KAP query, notable stocks, macro, LLM commentary, upsert)
    - Wave 3: APScheduler cron at 06:30 Europe/Istanbul weekdays
  </what-built>
  <how-to-verify>
    1. Run the full test suite:
       `cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/test_daily_briefing.py -v`
       Expected: 8 tests, ALL xpass (not xfail, not error, not failed)

    2. Run regression suite:
       `cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/ -q`
       Expected: All pre-existing tests still pass

    3. Confirm the briefing endpoint is registered:
       Start the app locally (if DB is available): `uvicorn app.main:app --reload`
       `curl http://localhost:8000/api/briefing/today`
       Expected: 404 JSON `{"detail": "Brifing henüz üretilmedi"}` (no record yet — correct behavior)

    4. Confirm the scheduler job exists at startup (check logs):
       Should see: "TETİKLENDİ: Günlük sabah brifing üretimi" at 06:30 on a weekday, or test via:
       `python3 -c "from app.main import scheduler; print([j.func.__name__ for j in scheduler.get_jobs()])"`
       Should include `generate_daily_briefing`

    5. Confirm no new files were created outside the plan scope:
       Plan scope: model_daily_briefing.py, api/briefing.py, services/briefing_generator.py, models/__init__.py, main.py, tests/test_daily_briefing.py
  </how-to-verify>
  <resume-signal>Type "approved" if all 8 tests xpass and the briefing endpoint returns 404. Describe any issues otherwise.</resume-signal>
</task>

</tasks>

<verification>
Full phase acceptance:
```
cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && \
  /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/test_daily_briefing.py -v
```

Expected final output:
```
XPASS tests/test_daily_briefing.py::test_daily_briefing_model_fields
XPASS tests/test_daily_briefing.py::test_briefing_today_endpoint_404
XPASS tests/test_daily_briefing.py::test_briefing_today_endpoint_200
XPASS tests/test_daily_briefing.py::test_notable_stocks_algorithm
XPASS tests/test_daily_briefing.py::test_daily_commentary_model
XPASS tests/test_daily_briefing.py::test_briefing_cron_registered
XPASS tests/test_daily_briefing.py::test_briefing_upsert
[and test_briefing_llm_failure_partial if implemented in Wave 2]
8 xpassed
```
</verification>

<success_criteria>
- `main.py` registers `generate_daily_briefing` with `timezone="Europe/Istanbul"` explicitly
- `test_briefing_cron_registered` xpasses
- All 8 Wave-0 stubs now xpass
- Full pytest suite passes with no regressions
- Human checkpoint approved
</success_criteria>

<rollback>
Revert the two changes to `main.py` (remove the generate_daily_briefing import and the scheduler.add_job call). `test_briefing_cron_registered` returns to xfail. All other tests remain xpass.
</rollback>

<output>
After completion, create `.planning/phases/04-ai-daily-briefing/plans/04-03-SUMMARY.md` with:
- File modified: backend/app/main.py
- Changes: module-level import of generate_daily_briefing + scheduler.add_job cron registration
- Cron: weekdays 06:30 Europe/Istanbul
- Phase gate: all 8 test_daily_briefing stubs xpass
- BREF-01 through BREF-05: all complete
</output>
