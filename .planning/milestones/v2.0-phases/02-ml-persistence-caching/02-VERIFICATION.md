---
status: passed
phase: 02-ml-persistence-caching
date: 2026-04-17
score: 3/3 requirements verified
---

# Phase 02: ML Persistence + Caching — Verification Report

**Phase Goal:** The system does not retrain XGBoost on every call and does not hammer yfinance or LLM APIs with redundant requests.
**Verified:** 2026-04-17
**Status:** PASSED

---

## MLCA-01: XGBoost Persistence + APScheduler Retrain

| Check | Status | Evidence |
|---|---|---|
| `save_model()` exists in ml.py | VERIFIED | Lines 58–63: saves `.ubj` via `model.save_model()` and `.joblib` via `joblib.dump()` |
| `load_model()` exists in ml.py | VERIFIED | Lines 65–75: loads both files, returns `(None, None)` if absent |
| `preload_all_models()` exists | VERIFIED | Lines 77–91: scans `MODEL_DIR` for `*_xgb.ubj`, loads all into `self._models` |
| `backend/models/` directory exists | VERIFIED | Directory present at `backend/models/` |
| `preload_all_models()` called in lifespan | VERIFIED | `main.py` line 131: `loaded_count = ml_engine.preload_all_models()` |
| Weekly cron job (`day_of_week="sun"`) | VERIFIED | `main.py` line 159: `scheduler.add_job(background_xgb_retrain, "cron", day_of_week="sun", hour=2, minute=0)` |
| `_train_and_predict()` uses in-memory cache first | VERIFIED | Lines 181–185: checks `self._models[symbol]` before training from scratch |

**Conclusion:** XGBoost is persisted to disk, preloaded at startup, served from in-memory cache on subsequent calls, and retrained weekly via APScheduler. No retrain-on-every-call.

---

## MLCA-02: yfinance Result Cache

| Check | Status | Evidence |
|---|---|---|
| `diskcache` imported and initialized | VERIFIED | `data_collector.py` line 11: `import diskcache`; line 35: `_yf_cache = diskcache.Cache(YFINANCE_CACHE_DIR)` |
| `get_ticker_history()` uses cache with 300s TTL | VERIFIED | Lines 38–53: cache key `history:{symbol}:{period}`, `expire=300` |
| `get_ticker_info()` uses cache with 86400s TTL | VERIFIED | Lines 56–71: cache key `info:{symbol}`, `expire=86400` |
| Empty DataFrame guard | VERIFIED | Line 51: `if not hist.empty:` — empty DataFrames are not cached |
| Empty dict guard for info | VERIFIED | Line 69: `if info:` — empty dicts are not cached |
| `get_ticker_history()` used throughout DataCollector | VERIFIED | Lines 109, 159, 242: all yfinance calls route through the cached helper |

**Conclusion:** All yfinance calls are wrapped with result-level diskcache. Price TTL is 300s, fundamental TTL is 86400s. Empty responses are not cached.

---

## MLCA-03: LLM Result Cache

| Check | Status | Evidence |
|---|---|---|
| `diskcache` imported and initialized | VERIFIED | `llm_sentiment.py` lines 4, 18: `_llm_cache = diskcache.Cache(LLM_CACHE_DIR)` |
| Cache key includes `hash(title)` | VERIFIED | Line 75: `cache_key = f"analysis:{symbol}:{date_str}:{hash(title)}"` |
| TTL is 1800 seconds | VERIFIED | Line 122: `_llm_cache.set(cache_key, result, expire=1800)` |
| Cache checked before API call | VERIFIED | Lines 77–79: `cached = _llm_cache.get(cache_key)` with early return |
| Cache populated after successful API call | VERIFIED | Line 122: set inside the `try` block after `result` is built |

**Conclusion:** LLM results are cached with a hash of the title in the key and a 30-minute TTL. API is not called for identical requests within the window.

---

## Test Evidence

```
14 passed, 6 xpassed, 2 warnings in 2.96s
```

Matches expected: 14 passed, 6 xpassed, 0 failed.

---

## Anti-Patterns

None found. No placeholder returns, no empty stubs, no TODO/FIXME markers in the three requirement files.

---

_Verified: 2026-04-17_
_Verifier: Claude (gsd-verifier)_
