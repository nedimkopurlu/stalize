# Phase 2: ML Persistence + Caching - Context

**Gathered:** 2026-04-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Add model persistence and two-layer HTTP/result caching so the backend stops retraining XGBoost on every call and stops hammering yfinance/DeepSeek with redundant requests. No new features, no UI changes.

Requirements in scope: MLCA-01, MLCA-02, MLCA-03.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion

Infrastructure-only phase — all implementation choices are at Claude's discretion within the library constraints specified in requirements.

Key constraints from REQUIREMENTS.md (already decided):
- MLCA-01: XGBoost model persistence in .ubj format; load at startup; weekly APScheduler retrain job
- MLCA-02: **requests-cache incompatible with yfinance 0.2.54+ (curl_cffi conflict — session injection raises RuntimeError).** Use diskcache result-level caching instead: wrap ticker.history() with 5min TTL and ticker.info with 24h TTL. Functionally equivalent — eliminates redundant Yahoo API calls.
- MLCA-03: diskcache library for LLM analysis results; 30min TTL; per-stock key

Implementation notes:
- XGBoost model files: store in `backend/models/` directory (create if missing)
- First startup with no saved model: train from scratch, then save
- Startup load: in `main.py` lifespan alongside existing `init_db()` call
- Weekly retrain: APScheduler cron job (e.g., Sunday 02:00) — add to existing scheduler in main.py
- requests-cache: install as session-level cache; yfinance uses requests internally so patching works
- diskcache: per-stock key format `analysis:{ticker}:{date}`; TTL 30min
- No admin endpoints needed for cache management in this phase

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/services/ml.py` — `MLAnalysisEngine` class with `xgb_params`; trains with `train_and_predict()` method
- `backend/app/main.py` lifespan — correct place for model load at startup (alongside `init_db()`)
- `backend/app/main.py` APScheduler — existing jobs (KAP 5min, TCMB 2h, TUIK daily 9:00, audit 18:05) — add weekly retrain alongside
- `backend/app/services/llm_sentiment.py` — DeepSeek analysis calls; where to add diskcache wrapper

### Established Patterns
- XGBoost already guarded with try/except (XGBOOST_AVAILABLE flag) — maintain same guard
- Lifespan pattern in main.py: `async with asynccontextmanager` with `init_db()` and scheduler start

### Integration Points
- `ml.py` `train_and_predict()` — add save-to-disk after training, load-from-disk at init
- `llm_sentiment.py` analysis method — wrap with diskcache check before calling DeepSeek
- `requirements.txt` — add `requests-cache`, `diskcache` (check if already present)

</code_context>

<specifics>
## Specific Ideas

- requirements.txt currently has NO requests-cache or diskcache — both need to be added
- XGBoost .ubj format: `model.save_model("models/xgb_model.ubj")` / `model.load_model(...)`
- Cache invalidation: time-based only (TTL) — no manual cache bust endpoints needed

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-ml-persistence-caching*
*Context gathered: 2026-04-17 (infrastructure phase — auto-generated)*
