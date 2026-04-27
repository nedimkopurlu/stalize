# Phase 03: LLM Infrastructure — Validation Strategy

**Status:** Wave 0 complete
**Phase:** 03-llm-infrastructure
**Test file:** `backend/tests/test_llm_infrastructure.py`

---

## Quick Run

```bash
cd backend && /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/test_llm_infrastructure.py -x -q
```

## Full Suite

```bash
cd backend && /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/ -x -q
```

---

## Requirement → Test Mapping

| Requirement | Tests |
|-------------|-------|
| LLMI-01 | `test_stock_analysis_model_valid`, `test_stock_analysis_model_invalid_karar`, `test_instructor_integration`, `test_legacy_dict_adapter` |
| LLMI-02 | `test_semaphore_limits_concurrency` |
| LLMI-03 | `test_staleness_warning_set_when_old`, `test_no_staleness_warning_fresh` |

---

## Phase Gate Condition

All 7 tests pass (not xfail) AND full `pytest tests/` suite is green.

At Wave 0: all 7 tests are `xfail` (strict=True) — this keeps the suite green while implementation is pending.

As each Wave lands:
- **Wave 1** (LLMI-01): `test_stock_analysis_model_valid`, `test_stock_analysis_model_invalid_karar`, `test_instructor_integration`, `test_legacy_dict_adapter` flip from xfail → PASSED
- **Wave 2** (LLMI-02): `test_semaphore_limits_concurrency` flips from xfail → PASSED
- **Wave 3** (LLMI-03): `test_staleness_warning_set_when_old`, `test_no_staleness_warning_fresh` flip from xfail → PASSED

---

## Wave Progress Tracker

| Wave | Requirement | Status |
|------|-------------|--------|
| 0    | Scaffold    | DONE   |
| 1    | LLMI-01     | pending |
| 2    | LLMI-02     | pending |
| 3    | LLMI-03     | pending |

---

## Note: test_llm_cache.py Migration (Wave 1)

After Wave 1 migrates `analyze()` return type to `StockAnalysis`, the `make_mock_response` helper in `test_llm_cache.py` must be updated. Specifically:

- `service.client.chat.completions.create` now returns a `StockAnalysis` object (not an AsyncOpenAI response)
- This is because `_patched_client` (the instructor-wrapped client) is used for the API call, not `service.client` directly
- Wave 1 task must update `test_llm_cache.py` accordingly to keep the cache test suite green
