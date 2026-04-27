---
phase: 03-llm-infrastructure
plan_id: "03-02"
title: "LLMI-02: asyncio.Semaphore(5) concurrency guard"
requirement: LLMI-02
wave: 2
estimated_minutes: 20
autonomous: true
depends_on: ["03-01"]
files_modified:
  - backend/app/services/llm_sentiment.py
must_haves:
  truths:
    - "_llm_semaphore = asyncio.Semaphore(5) exists at module level in llm_sentiment.py"
    - "The semaphore wraps only the live API call — cache reads are outside the semaphore block"
    - "More than 5 concurrent analyze() calls queue correctly: the 6th call starts only after one of the first 5 finishes"
  artifacts:
    - path: "backend/app/services/llm_sentiment.py"
      provides: "Module-level _llm_semaphore; semaphore wraps _patched_client call"
      contains: "_llm_semaphore = asyncio.Semaphore(5)"
  key_links:
    - from: "analyze()"
      to: "_llm_semaphore"
      via: "async with _llm_semaphore: await self._patched_client.chat.completions.create(...)"
      pattern: "async with _llm_semaphore"
---

<objective>
Verify and confirm that `_llm_semaphore = asyncio.Semaphore(5)` is correctly placed as a module-level singleton in `llm_sentiment.py` and that `async with _llm_semaphore:` wraps only the live API call inside `analyze()`.

Purpose: Wave 1 wrote the complete rewrite including the semaphore. This plan's job is to confirm placement is correct, add the `test_semaphore_limits_concurrency` test passing, and ensure the semaphore is NOT around the cache read.
Output: test_semaphore_limits_concurrency PASSES.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@.planning/phases/03-llm-infrastructure/03-CONTEXT.md
@backend/app/services/llm_sentiment.py
@backend/tests/test_llm_infrastructure.py

<interfaces>
<!-- From Wave 1 (03-01) output — executor reads the actual file, not this summary -->
Module-level after Wave 1:
  _llm_cache: diskcache.Cache
  _llm_semaphore: asyncio.Semaphore(5)   ← must exist here
  _STALENESS_THRESHOLD: timedelta(minutes=15)

analyze() structure:
  1. No-client fallback (before semaphore)
  2. Cache check (before semaphore — cache hits must NOT acquire semaphore slot)
  3. Staleness detection (before semaphore)
  4. async with _llm_semaphore:   ← semaphore entry point
       result = await self._patched_client.chat.completions.create(...)
  5. result.staleness_warning = staleness_warning (after semaphore)
  6. _llm_cache.set(...)
  7. return result
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Verify semaphore placement and make test_semaphore_limits_concurrency pass</name>
  <files>backend/app/services/llm_sentiment.py, backend/tests/test_llm_infrastructure.py</files>
  <behavior>
    - _llm_semaphore is at module level (not inside __init__ or analyze)
    - isinstance(_llm_semaphore, asyncio.Semaphore) is True
    - _llm_semaphore._value == 5 at module import time
    - async with _llm_semaphore: appears AFTER cache check in analyze() source
    - async with _llm_semaphore: appears BEFORE _patched_client.chat.completions.create call
  </behavior>
  <action>
**Step 1 — Inspect llm_sentiment.py (already written in Wave 1):**

Read the current `backend/app/services/llm_sentiment.py` and verify:
1. `_llm_semaphore = asyncio.Semaphore(5)` is present at module level (after `_llm_cache = ...`)
2. Inside `analyze()`, `async with _llm_semaphore:` wraps the `_patched_client.chat.completions.create(...)` call
3. The cache check (`_llm_cache.get(cache_key)`) appears BEFORE the `async with _llm_semaphore:` block

If any placement is wrong, correct it. The target structure is:

```python
# Module level (top of file, after diskcache import):
_llm_cache = diskcache.Cache(LLM_CACHE_DIR)           # Phase 2: MLCA-03
_llm_semaphore = asyncio.Semaphore(5)                  # Phase 3: LLMI-02

# Inside analyze():
#   1. No-client early return
#   2. cache check → return cached  (no semaphore acquired)
#   3. staleness detection
#   4. prompt assembly
#   5. async with _llm_semaphore:
#          result = await self._patched_client...create(response_model=StockAnalysis, ...)
#   6. result.staleness_warning = staleness_warning
#   7. _llm_cache.set(...)
#   8. return result
```

**Step 2 — Update test_semaphore_limits_concurrency in test_llm_infrastructure.py:**

The current xfail stub checks `sem._value == 5`. Remove the `@pytest.mark.xfail` decorator from `test_semaphore_limits_concurrency` so it becomes a live test. The test body already imports `app.services.llm_sentiment` and checks `_llm_semaphore._value == 5` — this is correct.

The updated test (remove xfail decorator only):
```python
# NO @pytest.mark.xfail decorator — this test should now PASS
def test_semaphore_limits_concurrency():
    """Module exposes _llm_semaphore = asyncio.Semaphore(5)."""
    import app.services.llm_sentiment as ls
    assert hasattr(ls, "_llm_semaphore"), "_llm_semaphore missing from module"
    sem = ls._llm_semaphore
    assert isinstance(sem, asyncio.Semaphore)
    assert sem._value == 5
```

Note: `sem._value` is a private attribute of asyncio.Semaphore. It is the internal counter and equals the initial value when no slots are acquired. This is stable in Python 3.9–3.12 stdlib implementation. If `_value` is not accessible (alternative asyncio implementations), fall back to checking `sem._bound_value` or skip the value assertion and only check `isinstance`.
  </action>
  <verify>
    <automated>cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/test_llm_infrastructure.py::test_semaphore_limits_concurrency -v 2>&1 | tail -10</automated>
  </verify>
  <done>test_semaphore_limits_concurrency PASSES (not xfail). `grep -n "_llm_semaphore" backend/app/services/llm_sentiment.py` shows the declaration at a line before the class definition AND `async with _llm_semaphore:` inside analyze().</done>
</task>

</tasks>

<verification>
cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/test_llm_infrastructure.py::test_semaphore_limits_concurrency tests/test_llm_cache.py -v 2>&1 | tail -10

# Also confirm placement with grep:
grep -n "_llm_semaphore\|async with _llm_semaphore\|cached = _llm_cache" /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend/app/services/llm_sentiment.py
</verification>

<success_criteria>
- test_semaphore_limits_concurrency PASSES (not xfail, not ERROR)
- `_llm_semaphore = asyncio.Semaphore(5)` line number is lower than `class DeepSeekSentimentService:` line number in the file
- `async with _llm_semaphore:` line number is greater than `cached = _llm_cache.get(cache_key)` line number in analyze()
- test_llm_cache.py still green
</success_criteria>

<output>
After completion, create `.planning/phases/03-llm-infrastructure/03-02-SUMMARY.md` with:
- Confirmed line numbers for _llm_semaphore declaration and async with block
- Test result
- Note: semaphore outside cache block (cache hits free, no slot acquired)
</output>
