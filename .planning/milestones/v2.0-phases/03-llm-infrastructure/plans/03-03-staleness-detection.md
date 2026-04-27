---
phase: 03-llm-infrastructure
plan_id: "03-03"
title: "LLMI-03: as_of timestamp + staleness_warning"
requirement: LLMI-03
wave: 2
estimated_minutes: 25
autonomous: true
depends_on: ["03-01"]
files_modified:
  - backend/app/services/llm_sentiment.py
  - backend/tests/test_llm_infrastructure.py
must_haves:
  truths:
    - "analyze() accepts as_of: Optional[datetime] = None parameter"
    - "Every prompt assembled by analyze() includes VERİ TARİHİ: {as_of_str} as the first line"
    - "If as_of is more than 15 minutes before datetime.now(UTC), result.staleness_warning is a non-empty string containing 'dakika'"
    - "If as_of is less than 15 minutes before datetime.now(UTC), result.staleness_warning is None"
    - "staleness_warning is set AFTER instructor returns — the LLM is never asked to generate it"
    - "Naive as_of datetimes are normalized to UTC before age computation"
  artifacts:
    - path: "backend/app/services/llm_sentiment.py"
      provides: "as_of param, staleness detection block, VERİ TARİHİ in prompt"
      contains: "_STALENESS_THRESHOLD = timedelta(minutes=15)"
  key_links:
    - from: "analyze() staleness block"
      to: "result.staleness_warning"
      via: "staleness_warning set before return; injected after instructor call"
      pattern: "result.staleness_warning = staleness_warning"
---

<objective>
Verify and confirm that all three staleness-related behaviors from LLMI-03 are correctly implemented in `analyze()`: the `as_of` parameter is accepted, `VERİ TARİHİ` appears in every prompt, and `staleness_warning` is set programmatically (not by the LLM) when data age exceeds 15 minutes.

Purpose: Callers can now pass `as_of=news_timestamp` when analyzing stale news events. The response will carry a human-readable warning that downstream UI layers can surface.
Output: test_staleness_warning_set_when_old and test_no_staleness_warning_fresh both PASS.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@.planning/phases/03-llm-infrastructure/03-CONTEXT.md
@backend/app/services/llm_sentiment.py
@backend/tests/test_llm_infrastructure.py

<interfaces>
<!-- Staleness detection pattern from RESEARCH.md — must match implementation -->

_STALENESS_THRESHOLD = timedelta(minutes=15)   # module-level constant

Inside analyze(), before prompt assembly:
  now = datetime.now(timezone.utc)
  staleness_warning = None
  if as_of is not None:
      if as_of.tzinfo is None:
          as_of = as_of.replace(tzinfo=timezone.utc)   # normalize naive datetimes
      age = now - as_of
      if age > _STALENESS_THRESHOLD:
          staleness_warning = f"Veri {int(age.total_seconds() // 60)} dakikadan eski"

  as_of_str = (as_of or now).strftime("%Y-%m-%d %H:%M UTC")
  prompt = f"VERİ TARİHİ: {as_of_str}\n..."

After instructor returns:
  result.staleness_warning = staleness_warning   # injects into StockAnalysis
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Verify staleness implementation and activate the two staleness tests</name>
  <files>backend/app/services/llm_sentiment.py, backend/tests/test_llm_infrastructure.py</files>
  <behavior>
    - analyze(as_of=20min_ago) → result.staleness_warning is not None and contains "dakika"
    - analyze(as_of=5min_ago) → result.staleness_warning is None
    - analyze(as_of=None) → staleness_warning is None (no as_of means no staleness check)
    - analyze() prompt string starts with "VERİ TARİHİ:"
    - Naive as_of is normalized: as_of.replace(tzinfo=timezone.utc) before age calculation
    - staleness_warning is set AFTER the async with _llm_semaphore block, not inside it
  </behavior>
  <action>
**Step 1 — Inspect llm_sentiment.py (already written in Wave 1):**

Read `backend/app/services/llm_sentiment.py` and verify all of the following are present and correctly ordered:

1. `_STALENESS_THRESHOLD = timedelta(minutes=15)` at module level
2. `analyze()` signature includes `as_of: Optional[datetime] = None`
3. Staleness detection block exists before prompt assembly:
   - `now = datetime.now(timezone.utc)` (NOT `datetime.utcnow()` — deprecated)
   - `if as_of is not None:` with timezone normalization
   - `age = now - as_of`
   - `if age > _STALENESS_THRESHOLD:` sets staleness_warning string
4. `as_of_str = (as_of or now).strftime(...)` used in prompt
5. `prompt` starts with `f"VERİ TARİHİ: {as_of_str}\n"`
6. `result.staleness_warning = staleness_warning` appears AFTER the `async with _llm_semaphore:` block exits

If any of the above is missing or misordered, fix it.

**Step 2 — Activate the two staleness tests in test_llm_infrastructure.py:**

Remove the `@pytest.mark.xfail(...)` decorator from:
- `test_staleness_warning_set_when_old`
- `test_no_staleness_warning_fresh`

These tests already mock `_patched_client.chat.completions.create` to return a `StockAnalysis` instance. The test for stale data passes `as_of = datetime.now(timezone.utc) - timedelta(minutes=20)`. The test for fresh data passes `as_of = datetime.now(timezone.utc) - timedelta(minutes=5)`.

Important: The mock returns a `StockAnalysis` object. After the semaphore block, `analyze()` mutates `result.staleness_warning = staleness_warning`. The test then asserts the staleness_warning on the returned object. This chain must work — verify the mock's returned StockAnalysis is the same object that gets mutated (it is, since instructor returns the same object reference).

**Step 3 — Edge case: naive datetime normalization**

Verify the implementation handles `as_of` without tzinfo:
```python
if as_of.tzinfo is None:
    as_of = as_of.replace(tzinfo=timezone.utc)
```
This must be present. If missing, `now - as_of` will raise `TypeError: can't subtract offset-naive and offset-aware datetimes`.
  </action>
  <verify>
    <automated>cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/test_llm_infrastructure.py::test_staleness_warning_set_when_old tests/test_llm_infrastructure.py::test_no_staleness_warning_fresh -v 2>&1 | tail -15</automated>
  </verify>
  <done>test_staleness_warning_set_when_old PASSES. test_no_staleness_warning_fresh PASSES. Neither reports xfail.</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>
Complete Phase 3 implementation across llm_sentiment.py:
- LLMI-01: StockAnalysis Pydantic model, instructor integration, _to_legacy_dict, system prompt updated
- LLMI-02: _llm_semaphore = asyncio.Semaphore(5) at module level, wraps only the live API call
- LLMI-03: as_of parameter, VERİ TARİHİ in prompt, staleness_warning set post-instructor
- All 4 caller files updated with _to_legacy_dict
- test_llm_infrastructure.py: 5 of 7 tests PASS, 2 may remain xfail (test_instructor_integration and test_legacy_dict_adapter should also pass after Wave 1)
  </what-built>
  <how-to-verify>
Run the full infrastructure test suite:
```bash
cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/test_llm_infrastructure.py tests/test_llm_cache.py -v
```

Expected: All 7 tests in test_llm_infrastructure.py PASS (not xfail). All 3 tests in test_llm_cache.py PASS.

Then run the full suite to check for regressions:
```bash
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/ -x -q
```

Expected: All existing tests pass. No new failures.
  </how-to-verify>
  <resume-signal>Type "approved" if all tests pass, or describe which tests failed and their error messages.</resume-signal>
</task>

</tasks>

<verification>
cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/test_llm_infrastructure.py -v 2>&1 | tail -20

# Confirm staleness threshold constant:
grep -n "_STALENESS_THRESHOLD\|VERİ TARİHİ\|staleness_warning\|as_of" /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend/app/services/llm_sentiment.py
</verification>

<success_criteria>
- test_staleness_warning_set_when_old PASSES
- test_no_staleness_warning_fresh PASSES
- All 7 tests in test_llm_infrastructure.py PASS (none remain xfail)
- Full `pytest tests/` suite green (no regressions in test_llm_cache.py, test_kap_parser.py, etc.)
- `grep "VERİ TARİHİ" backend/app/services/llm_sentiment.py` returns a match in the prompt string
- `grep "result.staleness_warning = staleness_warning" backend/app/services/llm_sentiment.py` returns a match after the semaphore block
</success_criteria>

<output>
After completion, create `.planning/phases/03-llm-infrastructure/03-03-SUMMARY.md` with:
- Confirmation of all LLMI-01/02/03 implementation points
- Final pytest results (test counts)
- List of files modified across all Phase 3 plans
- Note any edge cases handled (naive datetime normalization, ValidationError fallback, Mode.JSON not JSON_SCHEMA)
</output>
