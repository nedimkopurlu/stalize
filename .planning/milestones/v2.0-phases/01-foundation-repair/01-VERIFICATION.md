---
status: passed
phase: 01-foundation-repair
date: 2026-04-17
---

# Phase 01: Foundation Repair — Verification Report

**Phase Goal:** The codebase produces only real data — no silent fallbacks, no ignored config, no timezone ambiguity, and no bloat from unused 3-4 GB dependencies.
**Verified:** 2026-04-17
**Status:** PASSED

---

## Summary

All 5 foundation requirements are satisfied. The codebase is free of mock fallbacks, hardcoded weights, heavy ML dependencies, monolithic router files, and timezone-naive timestamps. The full test suite (3 passed, 6 xpassed) confirms correctness programmatically.

---

## Must-Haves Verification

| Requirement | Check | Status |
|---|---|---|
| FOND-01 | `kap_parser.py` contains no `_generate_mock_announcements` or `mock` fallback | VERIFIED |
| FOND-01 | `main.py` raises `RuntimeError` at startup if `feedparser` is missing | VERIFIED |
| FOND-02 | `scoring.py` contains no `BASE_WEIGHTS` constant | VERIFIED |
| FOND-02 | `scoring.py` imports from `app.core.config` and reads `WEIGHT_*` from `settings` | VERIFIED |
| FOND-03 | `requirements.txt` contains none of: `tensorflow`, `torch`, `transformers`, `sentencepiece` | VERIFIED |
| FOND-04 | `backend/app/api/endpoints.py` does not exist | VERIFIED |
| FOND-04 | `backend/app/api/` contains all 6 split routers: `stocks.py`, `macro.py`, `portfolio.py`, `intelligence.py`, `causal.py`, `admin.py` | VERIFIED |
| FOND-04 | `main.py` registers all 6 routers via `include_router` | VERIFIED |
| FOND-05 | `model_portfolio.py` uses `DateTime(timezone=True)` for all timestamp columns | VERIFIED |
| FOND-05 | `model_portfolio.py` uses `func.now()` as server default (no naive `datetime.utcnow`) | VERIFIED |

### Detail Notes

**FOND-01:** `grep` against `kap_parser.py` returned zero matches for `mock` or `generate_mock`. `main.py` lines 107-109 confirm the startup guard: `import feedparser` inside a try block raises `RuntimeError("feedparser is not installed...")` on import failure.

**FOND-02:** `scoring.py` has no `BASE_WEIGHTS`. Line 12 imports `settings` from `app.core.config`. Lines 46-51 read `settings.WEIGHT_TECHNICAL`, `WEIGHT_FUNDAMENTAL`, `WEIGHT_ML`, `WEIGHT_SENTIMENT`, `WEIGHT_CAUSAL`, `WEIGHT_MACRO` directly — all weight values are config-driven.

**FOND-03:** `requirements.txt` grep returned no output for any of the four heavy packages.

**FOND-04:** `endpoints.py` does not exist. The `api/` directory contains exactly: `__init__.py`, `admin.py`, `causal.py`, `intelligence.py`, `macro.py`, `portfolio.py`, `stocks.py`. `main.py` lines 165-170 register all 6 routers under `/api` prefix.

**FOND-05:** `model_portfolio.py` line 18: `generation_date = Column(DateTime(timezone=True), server_default=func.now(), ...)` and line 19: `target_date = Column(DateTime(timezone=True), ...)`. Both timestamp columns are timezone-aware with SQLAlchemy's server-side `func.now()`.

---

## Test Evidence

```
3 passed, 6 xpassed, 1 warning in 2.95s
```

Run: `cd backend && python3 -m pytest tests/ -q`

- 3 passed: standard assertion tests (includes `test_no_mock_method` from `tests/test_kap_parser.py`)
- 6 xpassed: tests marked `xfail` that now pass, indicating previously broken behavior is fixed
- 1 warning: Pydantic V2 deprecation for class-based config in `app/core/config.py` — non-blocking, does not affect runtime behavior

---

## Gaps

None.

---

_Verified: 2026-04-17_
_Verifier: Claude (gsd-verifier)_
