---
phase: "03"
plan: "03"
subsystem: llm-infrastructure
tags: [staleness, as_of, timestamp, llm, testing, LLMI-03]
dependency_graph:
  requires: [03-01, 03-02]
  provides: [llm-staleness-detection]
  affects: [llm_sentiment.py]
tech_stack:
  added: []
  patterns: [post-semaphore-injection, naive-datetime-normalization, programmatic-field-injection]
key_files:
  created: []
  modified:
    - backend/app/services/llm_sentiment.py
    - backend/tests/test_llm_infrastructure.py
decisions:
  - "staleness_warning injected after semaphore block exits — LLM never generates it, only the runtime staleness check does"
  - "Naive as_of datetimes normalized via as_of.replace(tzinfo=timezone.utc) before subtraction to avoid TypeError"
  - "datetime.now(timezone.utc) used (not deprecated datetime.utcnow()) for offset-aware now"
metrics:
  duration: "< 5 minutes"
  completed: "2026-04-17"
  tasks_completed: 1
  files_changed: 0
---

# Phase 03 Plan 03: LLMI-03 Staleness Detection Summary

Verified that `_STALENESS_THRESHOLD`, the `as_of` parameter, staleness detection block, `VERİ TARİHİ` prompt header, and post-semaphore `result.staleness_warning` injection are all correctly implemented in `llm_sentiment.py`. Confirmed both staleness tests pass as live (non-xfail) tests.

## Outcome

No code changes were required. The implementation was already fully correct as of plan 03-03 execution. Both staleness tests (`test_staleness_warning_set_when_old`, `test_no_staleness_warning_fresh`) were already active — no `@pytest.mark.xfail` decorators were present.

## LLMI-01 / LLMI-02 / LLMI-03 Implementation Confirmation

### LLMI-01: StockAnalysis Pydantic Model + instructor Integration

| Item | File | Line |
|------|------|------|
| `class StockAnalysis(BaseModel)` | `llm_sentiment.py` | 28 |
| `staleness_warning: Optional[str] = None` field | `llm_sentiment.py` | 34 |
| `__init__` accepts `ödül` unicode alias | `llm_sentiment.py` | 45-51 |
| `_to_legacy_dict(analysis)` adapter | `llm_sentiment.py` | 60-73 |
| `instructor.from_openai(..., mode=instructor.Mode.JSON)` | `llm_sentiment.py` | 99-102 |
| System prompt instructs LLM NOT to set `staleness_warning` | `llm_sentiment.py` | 127 |

**Edge case: Mode.JSON not JSON_SCHEMA** — DeepSeek does not support `Mode.JSON_SCHEMA` (causes HTTP 400). `instructor.Mode.JSON` is used exclusively.

**Edge case: ValidationError fallback** — if `instructor` is unavailable or raises `ImportError`/`AttributeError`, `_patched_client` falls back to the raw `AsyncOpenAI` client (line 108). A general `except Exception` in `analyze()` (line 201) returns a safe `StockAnalysis(karar="TUT", ...)` on any parse error.

### LLMI-02: asyncio.Semaphore(5) Concurrency Limit

| Item | File | Line |
|------|------|------|
| `_llm_semaphore = asyncio.Semaphore(5)` | `llm_sentiment.py` | 21 |
| Cache check before semaphore acquisition | `llm_sentiment.py` | 153-159 |
| `async with _llm_semaphore:` wraps only API call | `llm_sentiment.py` | 185-195 |

Cache hits short-circuit at line 159, never acquiring a semaphore slot.

### LLMI-03: as_of Timestamp + staleness_warning

| Item | File | Line |
|------|------|------|
| `_STALENESS_THRESHOLD = timedelta(minutes=15)` | `llm_sentiment.py` | 23 |
| `as_of: Optional[datetime] = None` in signature | `llm_sentiment.py` | 137 |
| `now = datetime.now(timezone.utc)` | `llm_sentiment.py` | 162 |
| Naive datetime normalization guard | `llm_sentiment.py` | 165-166 |
| `age = now - as_of` | `llm_sentiment.py` | 167 |
| `if age > _STALENESS_THRESHOLD:` staleness string | `llm_sentiment.py` | 168-171 |
| `as_of_str = (as_of or now).strftime(...)` | `llm_sentiment.py` | 173 |
| Prompt starts with `f"VERİ TARİHİ: {as_of_str}\n"` | `llm_sentiment.py` | 175 |
| `result.staleness_warning = staleness_warning` post-semaphore | `llm_sentiment.py` | 197 |

**Edge case: naive datetime normalization** — `as_of.tzinfo is None` check at line 165 normalizes naive datetimes with `.replace(tzinfo=timezone.utc)` before computing `age`. Without this, `now - as_of` raises `TypeError: can't subtract offset-naive and offset-aware datetimes`.

## Files Modified Across All Phase 3 Plans

| Plan | Files Modified |
|------|---------------|
| 03-00 | `backend/tests/test_llm_infrastructure.py` (xfail stubs created) |
| 03-01 | `backend/app/services/llm_sentiment.py` (StockAnalysis, instructor, _to_legacy_dict, callers) |
| 03-01 | `backend/tests/test_llm_infrastructure.py` (xfail stubs activated for LLMI-01 tests) |
| 03-01 | `backend/app/services/kap_parser.py` (migrated to _to_legacy_dict) |
| 03-01 | `backend/app/services/sentiment.py` (migrated to _to_legacy_dict) |
| 03-01 | `backend/app/services/macro_news.py` (migrated to _to_legacy_dict) |
| 03-01 | `backend/app/services/market_intelligence.py` (migrated to _to_legacy_dict) |
| 03-02 | `backend/app/services/llm_sentiment.py` (semaphore already correct — no changes) |
| 03-03 | `backend/app/services/llm_sentiment.py` (staleness already correct — no changes) |
| 03-03 | `backend/tests/test_llm_infrastructure.py` (staleness tests already active — no changes) |

## Final Pytest Results

### Targeted staleness tests:
```
tests/test_llm_infrastructure.py::test_staleness_warning_set_when_old PASSED
tests/test_llm_infrastructure.py::test_no_staleness_warning_fresh PASSED

2 passed, 6 warnings in 0.86s
```

### Full suite:
```
21 passed, 6 xpassed, 7 warnings in 7.76s
```

All tests pass. No regressions.

## Deviations from Plan

None — plan executed exactly as written. The implementation was already fully correct. Both staleness tests were already active (no `@pytest.mark.xfail` decorators present).

## Known Stubs

None. All staleness fields are wired to real logic: `staleness_warning` is computed from actual `datetime.now(timezone.utc) - as_of` arithmetic, not placeholder values.

## Self-Check: PASSED

- `_STALENESS_THRESHOLD = timedelta(minutes=15)` confirmed at module level line 23
- `as_of: Optional[datetime] = None` confirmed in `analyze()` signature line 137
- `now = datetime.now(timezone.utc)` confirmed at line 162 (not deprecated `datetime.utcnow()`)
- Naive datetime normalization guard confirmed at lines 165-166
- `result.staleness_warning = staleness_warning` confirmed at line 197, after `async with _llm_semaphore:` block (lines 185-195)
- `VERİ TARİHİ: {as_of_str}` confirmed as first line of prompt at line 175
- Both staleness tests PASS as live tests (not xfail)
- Full suite: 21 passed, 6 xpassed, 0 failures
