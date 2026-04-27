# Phase 2: ML Persistence + Caching - Research

**Researched:** 2026-04-17
**Domain:** XGBoost model persistence, yfinance caching, diskcache LLM result caching, APScheduler
**Confidence:** HIGH (XGBoost, diskcache, APScheduler) / MEDIUM (yfinance caching — critical breaking-change finding)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Infrastructure-only phase — all implementation choices are at Claude's discretion within the library constraints specified in requirements.
- MLCA-01: XGBoost model persistence in .ubj format; load at startup; weekly APScheduler retrain job
- MLCA-02: requests-cache library for yfinance HTTP layer; price data 5min TTL; fundamental data 24h TTL
- MLCA-03: diskcache library for LLM analysis results; 30min TTL; per-stock key
- XGBoost model files: store in `backend/models/` directory (create if missing)
- First startup with no saved model: train from scratch, then save
- Startup load: in `main.py` lifespan alongside existing `init_db()` call
- Weekly retrain: APScheduler cron job (e.g., Sunday 02:00) — add to existing scheduler in main.py
- requests-cache: install as session-level cache; yfinance uses requests internally so patching works
- diskcache: per-stock key format `analysis:{ticker}:{date}`; TTL 30min
- No admin endpoints needed for cache management in this phase

### Claude's Discretion
All implementation choices are at Claude's discretion within the library constraints above.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MLCA-01 | XGBoost models saved to disk (.ubj); loaded at startup; weekly APScheduler retrain | XGBRegressor.save_model/load_model API, `backend/models/` path strategy, lifespan hook, APScheduler cron trigger |
| MLCA-02 | yfinance HTTP layer cached with requests-cache (5min TTL for price, 24h TTL for fundamental) | CRITICAL: yfinance >=0.2.54 uses curl_cffi internally — requests-cache session injection is **blocked**; alternative strategy required (see Architecture section) |
| MLCA-03 | LLM analysis results cached with diskcache (30min TTL, per-stock key `analysis:{ticker}:{date}`) | diskcache Cache.set(key, value, expire=1800) pattern, wrap DeepSeekSentimentService.analyze() |
</phase_requirements>

---

## Summary

This phase adds three infrastructure layers to stop retraining XGBoost on every call and to stop hammering external APIs. XGBoost and diskcache are straightforward; yfinance caching has a confirmed breaking change that invalidates the session-injection approach assumed in CONTEXT.md.

**XGBoost (MLCA-01):** `XGBRegressor.save_model("file.ubj")` / `load_model("file.ubj")` work directly on the sklearn wrapper (confirmed in xgboost 2.1.x docs). The current code trains per-stock on each call — the fix wraps the per-stock model in a save/load cycle under `backend/models/{symbol}_xgb.ubj`. The `StandardScaler` must also be persisted alongside the model (see Architecture section — scaler is NOT saved by XGBoost's save_model).

**yfinance caching (MLCA-02):** CRITICAL finding: yfinance 0.2.54 (the pinned version) includes curl_cffi as a dependency and **actively raises an exception** when a `requests-cache` `CachedSession` is passed as the `session=` argument: `"request_cache sessions don't work with curl_cffi, which is necessary now for Yahoo API."` The session-injection approach will not work. The correct alternative is **result-level caching**: cache the pandas DataFrame returned by `ticker.history()` and `ticker.info` using diskcache, bypassing the HTTP layer entirely. This meets the spirit of MLCA-02 (reduce redundant API calls) without conflicting with yfinance internals.

**diskcache (MLCA-03):** Straightforward. `diskcache.Cache(directory)` with `cache.set(key, value, expire=seconds)` / `cache.get(key)`. Per-stock key `analysis:{ticker}:{date_str}` with 30min TTL (expire=1800). Inject at the top of `DeepSeekSentimentService.analyze()`.

**Primary recommendation:** Use diskcache for ALL three caching layers (XGBoost scaler persistence via joblib, yfinance result cache via diskcache, LLM cache via diskcache). Do not attempt requests-cache session injection with yfinance 0.2.54+.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| xgboost | 2.1.4 (pinned) | Model save/load via `.ubj` | Already installed; save_model/load_model are native XGBoost API |
| diskcache | 5.6.3 | Persistent key/value cache with TTL | Pure-Python, SQLite-backed, no daemon process, TTL built-in, used in LLM caching guides |
| joblib | 1.4.x (via scikit-learn dep) | Persist StandardScaler alongside XGBoost model | Already transitively installed via scikit-learn; standard for sklearn object serialization |
| apscheduler | 3.11.0 (pinned) | Weekly retrain cron trigger | Already installed and used in main.py |

### Do NOT Use

| Library | Reason |
|---------|--------|
| requests-cache | yfinance 0.2.54+ uses curl_cffi internally; passing a CachedSession raises RuntimeError |
| pickle directly | Not safe for cross-version sklearn objects; joblib is preferred |

**Version verification:**
```bash
pip show diskcache   # expect 5.6.x
pip show joblib      # expect 1.4.x (installed via scikit-learn)
```

**Installation — only new dependency:**
```bash
pip install diskcache==5.6.3
```

---

## Architecture Patterns

### Recommended Project Structure (additions only)

```
backend/
├── models/                     # NEW — XGBoost + scaler persisted files
│   ├── AKBNK_xgb.ubj           # per-stock XGBoost model
│   ├── AKBNK_scaler.joblib     # paired StandardScaler
│   └── .gitkeep                # keep directory in git, ignore *.ubj/*.joblib
├── app/
│   ├── services/
│   │   ├── ml.py               # MODIFIED — add save/load/retrain
│   │   ├── llm_sentiment.py    # MODIFIED — add diskcache wrapper
│   │   └── data_collector.py   # MODIFIED — add yfinance result cache
│   └── main.py                 # MODIFIED — add lifespan model load + weekly job
└── cache/                      # NEW — diskcache storage directory
    ├── llm/                    # LLM results cache (30min TTL)
    └── yfinance/               # yfinance result cache (5min / 24h TTL)
```

### Pattern 1: XGBoost Per-Stock Model Persistence

**What:** Each stock gets its own `{SYMBOL}_xgb.ubj` + `{SYMBOL}_scaler.joblib` pair saved under `backend/models/`. On startup, `MLAnalysisEngine.__init__` pre-loads all models found on disk into an in-memory dict. On predict, if a model is already loaded, skip training; if not (first run), train and save.

**Critical detail:** `XGBRegressor.save_model()` saves only the boosted tree. It does NOT save the `StandardScaler` state. The scaler must be saved separately with joblib.

**When to use:** After every training run, and on the weekly retrain job.

```python
# Source: xgboost 2.1.x official docs + sklearn joblib convention
import os
import joblib
import xgboost as xgb

MODEL_DIR = os.path.join(os.path.dirname(__file__), "../../models")

def _model_path(symbol: str) -> str:
    return os.path.join(MODEL_DIR, f"{symbol}_xgb.ubj")

def _scaler_path(symbol: str) -> str:
    return os.path.join(MODEL_DIR, f"{symbol}_scaler.joblib")

def save_model(symbol: str, model: xgb.XGBRegressor, scaler) -> None:
    os.makedirs(MODEL_DIR, exist_ok=True)
    model.save_model(_model_path(symbol))
    joblib.dump(scaler, _scaler_path(symbol))

def load_model(symbol: str):
    """Returns (model, scaler) or (None, None) if not found."""
    mp, sp = _model_path(symbol), _scaler_path(symbol)
    if not os.path.exists(mp) or not os.path.exists(sp):
        return None, None
    model = xgb.XGBRegressor()
    model.load_model(mp)
    scaler = joblib.load(sp)
    return model, scaler
```

**First-startup flow:**
```
load_model(symbol) → (None, None)
    → train from scratch
    → save_model(symbol, model, scaler)
    → use model for prediction
```

**Subsequent calls:**
```
load_model(symbol) → (model, scaler)
    → skip training
    → use loaded model for prediction
```

### Pattern 2: diskcache for LLM Results (MLCA-03)

**What:** Wrap `DeepSeekSentimentService.analyze()` with a cache check before calling the DeepSeek API. Key: `analysis:{ticker}:{date_str}`, TTL: 1800 seconds (30 min).

**When to use:** At the top of `analyze()`, before the API call.

```python
# Source: diskcache 5.6.1 official docs (grantjenks.com/docs/diskcache/tutorial.html)
import diskcache

CACHE_DIR = os.path.join(os.path.dirname(__file__), "../../cache/llm")
_cache = diskcache.Cache(CACHE_DIR)

async def analyze(self, title: str, summary: str = "", source: str = "Unknown",
                  symbol: str = None, event_type: str = None) -> Dict:
    from datetime import date
    date_str = date.today().isoformat()
    cache_key = f"analysis:{symbol}:{date_str}:{hash(title)}"

    cached = _cache.get(cache_key)
    if cached is not None:
        logger.debug(f"Cache hit: {cache_key}")
        return cached

    # ... existing DeepSeek API call ...
    result = await self._call_deepseek(title, summary, source)
    _cache.set(cache_key, result, expire=1800)
    return result
```

**Key design note:** The key includes `hash(title)` because the same `symbol` can have multiple news items in the same day. A flat `analysis:{ticker}:{date}` key would overwrite earlier results with later ones.

### Pattern 3: yfinance Result-Level Caching (MLCA-02 — alternative approach)

**What:** Cache the DataFrame/dict returned by yfinance at the Python level, not the HTTP level. Use diskcache with 5min TTL for price data (ticker.history) and 24h TTL for fundamental data (ticker.info).

**Why this instead of requests-cache:** yfinance 0.2.54 uses curl_cffi for all HTTP. Passing a `requests_cache.CachedSession` as `session=` raises: `"request_cache sessions don't work with curl_cffi."` There is no supported hook to intercept yfinance's HTTP at the requests layer.

```python
# Source: diskcache tutorial + yfinance data.py analysis
import diskcache
import yfinance as yf

YFINANCE_CACHE_DIR = os.path.join(os.path.dirname(__file__), "../../cache/yfinance")
_yf_cache = diskcache.Cache(YFINANCE_CACHE_DIR)

def get_ticker_history(yahoo_symbol: str, period: str = "5d") -> "pd.DataFrame":
    key = f"history:{yahoo_symbol}:{period}"
    cached = _yf_cache.get(key)
    if cached is not None:
        return cached
    ticker = yf.Ticker(yahoo_symbol)
    hist = ticker.history(period=period)
    _yf_cache.set(key, hist, expire=300)   # 5min TTL for price data
    return hist

def get_ticker_info(yahoo_symbol: str) -> dict:
    key = f"info:{yahoo_symbol}"
    cached = _yf_cache.get(key)
    if cached is not None:
        return cached
    ticker = yf.Ticker(yahoo_symbol)
    info = ticker.info or {}
    _yf_cache.set(key, info, expire=86400)  # 24h TTL for fundamental data
    return info
```

### Pattern 4: APScheduler Weekly Retrain Job

**What:** Add a cron job to `main.py` lifespan that runs every Sunday at 02:00 and retrains all per-stock XGBoost models.

**When to add:** In the lifespan block, alongside the existing `scheduler.add_job(...)` calls.

```python
# Source: APScheduler 3.11 docs (apscheduler.readthedocs.io/en/3.x/userguide.html)
# Pattern matches existing scheduler jobs in main.py

async def background_xgb_retrain():
    from app.services.ml import MLAnalysisEngine
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.stock import Stock
    logging.info("XGBoost Haftalık Retrain başlıyor...")
    try:
        engine = MLAnalysisEngine()
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Stock).where(Stock.is_active == True))
            stocks = result.scalars().all()
            for stock in stocks:
                await engine.retrain_and_save(db, stock)
        logging.info("XGBoost Haftalık Retrain tamamlandı")
    except Exception as e:
        logging.error(f"XGBoost Retrain Hatası: {e}")

# In lifespan, after existing scheduler.add_job calls:
scheduler.add_job(
    background_xgb_retrain,
    "cron",
    day_of_week="sun",
    hour=2,
    minute=0
)
```

### Pattern 5: Startup Model Load in Lifespan

**What:** At startup, pre-load all existing `.ubj` model files from `backend/models/` into `MLAnalysisEngine`'s in-memory dict. This ensures the first incoming request uses a loaded model rather than triggering a full retrain.

```python
# In main.py lifespan, after init_db:
async def load_ml_models_at_startup():
    from app.services.ml import ml_engine  # singleton
    ml_engine.preload_all_models()
    logging.info(f"XGBoost modelleri yüklendi: {len(ml_engine._models)} hisse")

# Call in lifespan before scheduler.start():
await load_ml_models_at_startup()
```

`MLAnalysisEngine` must be refactored to hold a singleton `_models: dict[str, tuple[XGBRegressor, StandardScaler]]` and expose a `preload_all_models()` method that scans `backend/models/*.ubj`.

### Anti-Patterns to Avoid

- **Saving one global XGBoost model for all 100 stocks:** Each stock has different price dynamics. Per-stock models are the correct pattern (already implied by the existing `analyze_stock(db, stock)` interface).
- **Retraining inside every `analyze_stock()` call at request time:** This is the current bug. With persistence, `analyze_stock()` must check if model is loaded before deciding whether to train.
- **Using `requests_cache.install_cache()` globally:** This patches the global `requests.Session`, but yfinance uses curl_cffi under the hood — the patch has no effect and adds confusion.
- **Storing diskcache under `/tmp`:** Diskcache under `/tmp` is wiped on reboot. Use a stable path under `backend/cache/`.
- **One diskcache instance per request:** Diskcache is SQLite-backed; open once as a module-level singleton, not per-call.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Scaler persistence | Custom pickle/json serializer | `joblib.dump` / `joblib.load` | joblib handles numpy arrays safely across versions; standard for sklearn ecosystem |
| Disk cache with TTL | Custom SQLite + time comparison | `diskcache.Cache` | TTL, eviction, concurrent access, and serialization already handled |
| XGBoost model serialization | Custom JSON of tree parameters | `model.save_model("file.ubj")` | UBJSON is the XGBoost-native format; preserves all tree structure, objective, and metadata |
| yfinance rate limiter | Custom sleep/retry loop | Diskcache result cache (5min TTL) | Prevents repeated API calls for same ticker within TTL window without fighting curl_cffi |

**Key insight:** All three serialization problems (model, scaler, API results) are already solved by well-maintained libraries. The only custom code needed is the glue: path construction, key building, TTL selection, and the startup preload loop.

---

## Common Pitfalls

### Pitfall 1: Scaler Not Persisted With Model

**What goes wrong:** `XGBRegressor.save_model("file.ubj")` saves only the boosted tree parameters. `StandardScaler` state (mean_, scale_ arrays) is not included. After a reload, calling `scaler.transform(X)` raises `NotFittedError` or produces wrong values.

**Why it happens:** XGBoost's `.ubj` format is a tree serialization format, not a Python object pickle. sklearn transformer objects have no serialization hook into it.

**How to avoid:** Always save the scaler with `joblib.dump(scaler, path)` immediately after `model.save_model(path)`. Treat the `.ubj` and `.joblib` files as a paired artifact — load both or load neither.

**Warning signs:** `NotFittedError: This StandardScaler instance is not fitted yet` on the first predict call after a restart.

### Pitfall 2: requests-cache with yfinance 0.2.54 Raises RuntimeError

**What goes wrong:** Installing requests-cache and calling `requests_cache.install_cache()` (or passing a `CachedSession` as `session=`) to yfinance does nothing or raises: `"request_cache sessions don't work with curl_cffi, which is necessary now for Yahoo API."`

**Why it happens:** yfinance 0.2.54 uses curl_cffi for all HTTP requests (required for Yahoo Finance anti-bot evasion). requests-cache patches the standard `requests` library, which yfinance no longer uses for its primary fetch path.

**How to avoid:** Use result-level caching (diskcache wrapping `ticker.history()` / `ticker.info`) instead of HTTP-layer caching. The functional outcome is identical: redundant calls to Yahoo Finance are eliminated.

**Warning signs:** Seeing Yahoo Finance requests in network logs despite requests-cache installation; `RuntimeError: request_cache sessions don't work with curl_cffi` at startup.

### Pitfall 3: Model Not Loaded Before First Request

**What goes wrong:** If `preload_all_models()` is called lazily (on first request) rather than in lifespan, the first request to each endpoint triggers a full XGBoost retrain. For 100 BIST stocks this can take tens of seconds, causing HTTP timeouts.

**Why it happens:** Lifespan startup is the correct place to do blocking I/O; request handlers must not block.

**How to avoid:** Call `ml_engine.preload_all_models()` explicitly inside `lifespan()` before `scheduler.start()` and before `yield`. Log the count of loaded models.

**Warning signs:** First-request latency spikes; "training from scratch" log lines appearing during request handling rather than during startup.

### Pitfall 4: diskcache Directory Not Created Before Use

**What goes wrong:** `diskcache.Cache("backend/cache/llm")` silently fails or raises `FileNotFoundError` if parent directory does not exist.

**Why it happens:** diskcache creates the leaf directory but not intermediate parents.

**How to avoid:** Call `os.makedirs(CACHE_DIR, exist_ok=True)` before instantiating `diskcache.Cache(CACHE_DIR)`.

**Warning signs:** `FileNotFoundError` at module import time.

### Pitfall 5: Relative Paths Break When uvicorn CWD Changes

**What goes wrong:** `MODEL_DIR = "models/"` resolves differently depending on where uvicorn is launched from (project root vs. `backend/` directory).

**Why it happens:** Relative paths are resolved against the process CWD, not the source file's location.

**How to avoid:** Use `__file__`-anchored absolute paths:
```python
import os
MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../models"))
```

**Warning signs:** `FileNotFoundError` on save/load in dev but not in prod (or vice versa), depending on launch directory.

### Pitfall 6: Weekly Retrain Job Blocks the Asyncio Event Loop

**What goes wrong:** `MLAnalysisEngine._train_and_predict()` uses `model.fit(X_scaled, y)` which is synchronous CPU-bound code. If run directly in an async APScheduler job on the event loop thread, it blocks all other async operations during training for all 100 stocks.

**Why it happens:** XGBoost's `fit()` is synchronous; calling it inside an `async def` does not make it non-blocking.

**How to avoid:** Wrap the training call in `asyncio.get_event_loop().run_in_executor(None, sync_train_func, ...)` for the retrain job, or accept the brief block for the current scale (100 stocks × lightweight model). The weekly job runs at 02:00 Sunday when no requests are expected. For now, the simpler `await asyncio.sleep(0)` interleave between stocks is sufficient to keep the event loop alive.

**Warning signs:** API becomes unresponsive during the Sunday 02:00 retrain window; timeout errors in logs.

---

## Code Examples

### XGBoost Save/Load (Verified Pattern)

```python
# Source: xgboost 2.1.x — XGBRegressor is sklearn wrapper; save_model works directly
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
import joblib

# --- SAVE ---
model = xgb.XGBRegressor(**params)
model.fit(X_scaled, y)
model.save_model("backend/models/AKBNK_xgb.ubj")   # .ubj extension → UBJSON format
joblib.dump(scaler, "backend/models/AKBNK_scaler.joblib")

# --- LOAD ---
model = xgb.XGBRegressor()          # empty instance; params restored from file
model.load_model("backend/models/AKBNK_xgb.ubj")
scaler = joblib.load("backend/models/AKBNK_scaler.joblib")

# --- PREDICT (no retraining) ---
X_current_scaled = scaler.transform(current_features.reshape(1, -1))
pred = model.predict(X_current_scaled)[0]
```

### diskcache TTL Cache (Verified Pattern)

```python
# Source: grantjenks.com/docs/diskcache/tutorial.html
import diskcache
import os

os.makedirs("/app/cache/llm", exist_ok=True)
cache = diskcache.Cache("/app/cache/llm")

# Set with TTL (seconds)
cache.set("analysis:AKBNK:2026-04-17:abc123", result_dict, expire=1800)  # 30 min

# Get (returns None on miss or expired)
cached = cache.get("analysis:AKBNK:2026-04-17:abc123")
if cached is None:
    # cache miss — call API
    pass
```

### APScheduler Cron — Sunday Weekly (Verified Pattern)

```python
# Source: APScheduler 3.x docs — matches existing pattern in main.py
scheduler.add_job(
    background_xgb_retrain,
    "cron",
    day_of_week="sun",
    hour=2,
    minute=0
)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| XGBoost JSON format | `.ubj` (UBJSON) is default in 2.1+ | XGBoost 2.1.0 (2024) | `.ubj` smaller and faster than `.json`; auto-detected by file extension |
| requests-cache session injection into yfinance | Not supported; use result-level caching | yfinance ~0.2.54 (2024) | curl_cffi migration broke session injection entirely |
| pickle for sklearn objects | joblib (scikit-learn standard) | sklearn 0.21+ | joblib handles large numpy arrays via memmap; safer across minor sklearn versions |

**Deprecated/outdated:**
- `yf.Ticker(symbol, session=requests_cache.CachedSession(...))`: Raises RuntimeError on yfinance 0.2.54+. Do not use.
- `xgb.Booster().save_model()` (native API) when using `XGBRegressor` (sklearn wrapper): Prefer `XGBRegressor.save_model()` directly; mixing APIs loses `best_iteration` and sklearn metadata.

---

## Open Questions

1. **Per-stock model memory footprint at startup**
   - What we know: 100 BIST stocks × (XGBRegressor with 100 estimators + StandardScaler) loaded into RAM
   - What's unclear: Total RAM usage — likely <50MB for 100 lightweight models but not measured
   - Recommendation: Add a startup log line reporting total models loaded and elapsed time; monitor first deployment

2. **yfinance result cache invalidation when Yahoo returns stale/empty data**
   - What we know: diskcache TTL is time-based only; no content-aware invalidation
   - What's unclear: If Yahoo returns an empty DataFrame during a 5min TTL window, the empty result is cached and served for up to 5 minutes
   - Recommendation: Do not cache empty DataFrames/dicts — add a guard: `if not hist.empty: cache.set(key, hist, expire=300)`

3. **diskcache thread-safety with APScheduler async jobs**
   - What we know: diskcache is SQLite-backed with WAL mode; concurrent reads are safe; concurrent writes use file locking
   - What's unclear: Whether the APScheduler retrain job writing model files simultaneously with request-time reads causes contention
   - Recommendation: Keep model files (joblib) and diskcache (SQLite) in separate directories as planned; they use different locking mechanisms

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (existing) |
| Config file | `backend/pytest.ini` (exists: `asyncio_mode = auto`) |
| Quick run command | `cd backend && pytest tests/test_ml_persistence.py tests/test_yf_cache.py tests/test_llm_cache.py -x -q` |
| Full suite command | `cd backend && pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MLCA-01 | `save_model` writes `.ubj` + `.joblib` files to disk | unit | `pytest tests/test_ml_persistence.py::test_save_creates_files -x` | ❌ Wave 0 |
| MLCA-01 | `load_model` restores model and scaler correctly (no retraining) | unit | `pytest tests/test_ml_persistence.py::test_load_restores_model -x` | ❌ Wave 0 |
| MLCA-01 | First startup with no model file trains from scratch then saves | unit | `pytest tests/test_ml_persistence.py::test_first_run_saves_model -x` | ❌ Wave 0 |
| MLCA-01 | APScheduler weekly job calls retrain on all active stocks | unit | `pytest tests/test_ml_persistence.py::test_weekly_retrain_job -x` | ❌ Wave 0 |
| MLCA-02 | yfinance result cache returns cached DataFrame on second call | unit | `pytest tests/test_yf_cache.py::test_price_cache_hit -x` | ❌ Wave 0 |
| MLCA-02 | price cache TTL is 300 seconds (5 min) | unit | `pytest tests/test_yf_cache.py::test_price_cache_ttl -x` | ❌ Wave 0 |
| MLCA-02 | fundamental (info) cache TTL is 86400 seconds (24h) | unit | `pytest tests/test_yf_cache.py::test_info_cache_ttl -x` | ❌ Wave 0 |
| MLCA-02 | Empty DataFrame is NOT cached (guard against Yahoo errors) | unit | `pytest tests/test_yf_cache.py::test_empty_not_cached -x` | ❌ Wave 0 |
| MLCA-03 | `analyze()` returns cached result on second call without hitting DeepSeek | unit | `pytest tests/test_llm_cache.py::test_cache_hit_skips_api -x` | ❌ Wave 0 |
| MLCA-03 | Cache key includes ticker + date + title hash | unit | `pytest tests/test_llm_cache.py::test_cache_key_format -x` | ❌ Wave 0 |
| MLCA-03 | Cache expires after 1800 seconds TTL | unit | `pytest tests/test_llm_cache.py::test_cache_expiry -x` | ❌ Wave 0 |

### Mock/Patch Strategy (No Real HTTP Calls)

All tests must mock external calls:

```python
# MLCA-01: mock db session to return synthetic PriceHistory rows
from unittest.mock import AsyncMock, patch, MagicMock

# MLCA-02: mock yf.Ticker to avoid real Yahoo HTTP calls
with patch("app.services.data_collector.yf.Ticker") as mock_ticker:
    mock_ticker.return_value.history.return_value = pd.DataFrame(...)
    mock_ticker.return_value.info = {"sector": "Finance"}
    ...

# MLCA-03: mock the AsyncOpenAI client to avoid real DeepSeek calls
with patch.object(service, "client") as mock_client:
    mock_client.chat.completions.create = AsyncMock(return_value=...)
    ...
```

### Sampling Rate

- **Per task commit:** `cd backend && pytest tests/test_ml_persistence.py tests/test_yf_cache.py tests/test_llm_cache.py -x -q`
- **Per wave merge:** `cd backend && pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `backend/tests/test_ml_persistence.py` — covers MLCA-01 (save/load/retrain/startup)
- [ ] `backend/tests/test_yf_cache.py` — covers MLCA-02 (price TTL, fundamental TTL, empty guard)
- [ ] `backend/tests/test_llm_cache.py` — covers MLCA-03 (cache hit, key format, TTL)
- [ ] `backend/models/.gitkeep` — ensures directory exists in git; `.gitignore` entry for `*.ubj` and `*.joblib`
- [ ] `backend/cache/` — directory must exist; `.gitignore` entry for `cache/llm/` and `cache/yfinance/`

---

## Sources

### Primary (HIGH confidence)
- [xgboost 2.1.x Model IO docs](https://xgboost.readthedocs.io/en/release_2.1.0/tutorials/saving_model.html) — save_model/load_model .ubj format, sklearn wrapper behavior
- [xgboost stable Python API](https://xgboost.readthedocs.io/en/stable/python/python_api.html) — XGBRegressor.save_model signature
- [diskcache 5.6.1 tutorial](https://grantjenks.com/docs/diskcache/tutorial.html) — Cache.set(key, value, expire=N), get, memoize
- [APScheduler 3.x user guide](https://apscheduler.readthedocs.io/en/3.x/userguide.html) — cron trigger, day_of_week parameter
- Direct code inspection: `backend/app/services/ml.py`, `backend/app/main.py`, `backend/app/services/llm_sentiment.py`, `backend/requirements.txt`

### Secondary (MEDIUM confidence)
- [yfinance GitHub issue #2496](https://github.com/ranaroussi/yfinance/issues/2496) — confirmed curl_cffi session rejection message; multiple affected users
- [yfinance GitHub issue #2486](https://github.com/ranaroussi/yfinance/issues/2486) — requests-cache CachedSession failure with yfinance 0.2.59
- [deepwiki yfinance caching architecture](https://deepwiki.com/ranaroussi/yfinance/6.2-caching-and-rate-limiting) — internal cookie/tz cache uses curl_cffi jars
- [xgboosting.com UBJ guide](https://xgboosting.com/save-xgboost-model-to-ubj-format-in-scikit-learn/) — confirms XGBRegressor.save_model() works with sklearn wrapper

### Tertiary (LOW confidence — flagged for validation)
- WebSearch synthesis on yfinance 0.2.54 specifically including curl_cffi: the exact version where curl_cffi became mandatory is stated as "around 0.2.32" in one source but "0.2.59+" in issue titles — the project's pinned 0.2.54 may or may not be affected. **Validation step:** Run `python -c "import yfinance as yf; t = yf.Ticker('AKBNK.IS'); import requests_cache; s = requests_cache.CachedSession(); t2 = yf.Ticker('AKBNK.IS', session=s)"` in the dev environment and observe whether an exception is raised.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries (xgboost, diskcache, joblib, apscheduler) are pinned/installed; APIs verified against official docs
- Architecture (XGBoost, diskcache, APScheduler): HIGH — patterns verified against official docs and existing code structure
- yfinance caching strategy: MEDIUM — breaking change confirmed by multiple GitHub issues and error messages; exact behavior on pinned 0.2.54 should be verified with one-liner test before committing to the alternative approach
- Pitfalls: HIGH — scaler gap is a known XGBoost SDK fact; path/CWD pitfall is observable from code; others are logic-derivable

**Research date:** 2026-04-17
**Valid until:** 2026-05-17 (xgboost/diskcache/apscheduler stable; yfinance moves fast — re-verify before upgrading past 0.2.54)
