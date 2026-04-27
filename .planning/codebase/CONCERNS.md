# Codebase Concerns

**Analysis Date:** 2026-04-16

---

## Security Considerations

**CORS Wildcard in Production:**
- Risk: Any origin can call the API, enabling cross-site request forgery from third-party pages.
- Files: `backend/app/main.py:152`
- Current mitigation: None — comment says "during development" but no production guard exists.
- Recommendations: Restrict `allow_origins` to specific domains at startup, ideally from `settings.CORS_ORIGINS` which already has a proper list configured.

**Unsanitized `sort_by` Parameter Exposed to `getattr`:**
- Risk: A caller can pass `sort_by=__class__` or any internal attribute name, and it will be resolved via `getattr(Stock, sort_by, …)`. While SQLAlchemy will reject non-column attributes at query time, this leaks attribute names in error messages and is not a safe pattern.
- Files: `backend/app/api/endpoints.py:358`, `backend/app/services/scoring.py:136`
- Current mitigation: The fallback is `Stock.overall_score`, so genuinely unknown attributes degrade gracefully.
- Recommendations: Whitelist allowed sort columns explicitly: `ALLOWED_SORT_COLS = {"overall_score", "technical_score", …}; assert sort_by in ALLOWED_SORT_COLS`.

**No Authentication or Authorization on Any Endpoint:**
- Risk: All API endpoints (including portfolio write operations and admin scan triggers like `/api/kap/scan`, `/api/macro/tcmb/scan`) are open with no token, session, or API key requirement.
- Files: `backend/app/api/endpoints.py` (entire file)
- Current mitigation: None. Relies purely on network-level access control.
- Recommendations: Add an API key dependency (`Depends(verify_api_key)`) at minimum for state-mutating endpoints.

**No Per-User Portfolio Isolation:**
- Risk: The `PortfolioItem` model has no `user_id` column. All portfolio items are shared across all users. Any caller to `GET /api/portfolio` sees the same unified portfolio.
- Files: `backend/app/models/portfolio.py`, `backend/app/api/endpoints.py:39`
- Current mitigation: Acceptable for a single-user local tool, breaks immediately for any multi-user scenario.
- Recommendations: Add `user_id` foreign key or session-based owner token before enabling multi-user access.

**DEBUG=True Hardcoded as Default:**
- Risk: `DEBUG: bool = True` is the default in config, which means `echo=settings.DEBUG` on the SQLAlchemy engine logs every SQL statement in production if the environment variable is not explicitly overridden.
- Files: `backend/app/core/config.py:16`, `backend/app/core/database.py:14`
- Current mitigation: Can be overridden via environment variable, but default is unsafe.
- Recommendations: Change default to `False` and explicitly enable in dev environment.

---

## Tech Debt

**ML Service Trains on Every Request (No Model Persistence):**
- Issue: `MLAnalysisEngine._train_and_predict` trains a fresh XGBoost model on every call for every stock. With 100 BIST stocks, each `collect_ml_predictions()` run trains 100 separate models that are discarded after prediction.
- Files: `backend/app/services/ml.py:96-116`
- Impact: Very high CPU usage during daily updates, slow data collection cycle, unpredictable per-call latency.
- Fix approach: Persist trained models to `settings.ML_MODEL_DIR` as pickle/joblib files, retrain on a schedule (weekly), and load cached model at prediction time.

**Heavy ML Dependencies Installed but Unused (`tensorflow`, `torch`, `transformers`):**
- Issue: `requirements.txt` includes `tensorflow==2.19.0`, `torch==2.6.0`, `transformers==4.51.3`, and `sentencepiece==0.2.0`. None of these are imported anywhere in `backend/app/`. The config has `LSTM_WINDOW_SIZE` and `LSTM_EPOCHS` settings that are also unused.
- Files: `backend/requirements.txt`, `backend/app/core/config.py:45-46`
- Impact: ~3-4GB of unnecessary install size, significantly longer CI/CD build times, possible import conflicts.
- Fix approach: Remove unused dependencies unless LSTM-based services are planned; move them to a `requirements-ml.txt` extras file.

**KAP/TCMB/TUIK Scan Endpoints Return Mock Data When Packages Missing:**
- Issue: `kap_parser.py` falls back to `self._generate_mock_announcements()` when `feedparser` is not installed. Production can silently run on fake data.
- Files: `backend/app/services/kap_parser.py:66-68`
- Impact: Silent data corruption; analysis scores calculated on fictional announcements.
- Fix approach: Raise a startup error if critical dependencies are absent; never fall back to mocks in a production code path.

**Incomplete Event Fusion — Indirect Impact Hardcoded to Zero:**
- Issue: `_compute_event_impacts` always sets `indirect_impact: 0` with two `# TODO` comments noting that knowledge graph propagation was never implemented.
- Files: `backend/app/services/event_fusion.py:308-316`
- Impact: Impact scores returned to the frontend are incomplete; the `/intelligence/fusion` and `/intelligence/impact-ranking` endpoints are partially functional.
- Fix approach: Integrate with `KnowledgeGraph.traverse_effects()` to propagate secondary impacts through causal edges.

**`get_model_portfolio` Handles Missing Model with Silent Mutation:**
- Issue: When no portfolio exists in DB, the endpoint calls `portfolio_optimizer.generate_daily_model()`, then immediately re-queries the DB. If the optimizer fails (returns `None` or doesn't persist), `model` remains `None` and the next `.id` access raises `AttributeError` — unhandled and will crash with a 500.
- Files: `backend/app/api/endpoints.py:209-217`
- Impact: Unhandled `AttributeError` on first access to model portfolio.
- Fix approach: Add null check after second query; raise a proper 503 with a clear message.

**Scoring Weights in Config vs. Service Are Inconsistent:**
- Issue: `settings` defines ensemble weights (`WEIGHT_TECHNICAL=0.20`, `WEIGHT_FUNDAMENTAL=0.25`, etc.) that total 0.90, while `ScoringEngine.BASE_WEIGHTS` hardcodes different values (technical=0.30, fundamental=0.20) and is never populated from `settings`. Two separate weight tables exist and diverge silently.
- Files: `backend/app/core/config.py:53-58`, `backend/app/services/scoring.py:22-28`
- Impact: Config-based weights are completely ignored; runtime behavior differs from what config implies.
- Fix approach: Remove weight constants from `config.py` or replace `ScoringEngine.BASE_WEIGHTS` with values from `settings`.

**N+1 Query Pattern in Price Data Collection:**
- Issue: `_collect_stock_prices` runs one `SELECT PriceHistory WHERE date=?` per row inside a loop over historical data. For a `5y` period with ~1,250 trading days × 100 symbols, this generates ~125,000 individual queries during `full_initial_load`.
- Files: `backend/app/services/data_collector.py:141-149`
- Impact: Initial data load is extremely slow; high DB CPU load.
- Fix approach: Bulk-fetch existing dates per stock in one query, then filter in Python before inserting.

**`get_portfolio` Mutates DB on Every Read:**
- Issue: The `GET /api/portfolio` endpoint writes back `current_price`, `current_value`, `profit_loss`, etc. to all `PortfolioItem` rows on every request, then calls `await db.commit()`. A simple read triggers a full write cycle.
- Files: `backend/app/api/endpoints.py:65-99`
- Impact: Any performance issue in the read path (e.g., under concurrency) can cause unnecessary DB write contention; makes caching the endpoint impossible.
- Fix approach: Separate read-time computation from persistence; only persist on a scheduled job or explicit update endpoint.

---

## Known Bugs

**`datetime.now()` Mixed with `datetime.utcnow()`:**
- Symptoms: Timestamps stored with `datetime.now()` (local time) in `data_collector.py` and `sentiment.py` will be incorrect when the server is not in UTC. These are compared to `datetime.utcnow()` time-filtered queries in endpoints.
- Files: `backend/app/services/data_collector.py:134`, `backend/app/services/sentiment.py:74`, vs. `backend/app/api/endpoints.py:488`
- Trigger: Deploy on a server with non-UTC timezone (e.g., Turkey's UTC+3).
- Workaround: Set the server `TZ=UTC` environment variable; fix by standardizing on `datetime.utcnow()` or timezone-aware datetimes throughout.

**`NewsItem.published_at` Has No Database Index:**
- Symptoms: `GET /api/macro/events` and event fusion both filter `NewsItem.published_at >= cutoff_time`. Without an index, this is a full table scan.
- Files: `backend/app/models/news.py:23`, `backend/app/api/endpoints.py:488`, `backend/app/services/event_fusion.py:71`
- Trigger: As news volume grows, these queries degrade to O(n) over the full `news_items` table.
- Workaround: None currently. Add `index=True` to the `published_at` column or a composite index `(stock_id, published_at)`.

**`PriceHistory.date` and `(stock_id, date)` Have No Composite Unique Constraint:**
- Symptoms: The deduplication check in `_collect_stock_prices` uses a `SELECT` per date to avoid duplicates, but there is no database-level unique constraint on `(stock_id, date)`. A race condition between concurrent collection runs could insert duplicate rows.
- Files: `backend/app/services/data_collector.py:141-149`, `backend/app/models/price.py`
- Trigger: Running two data collection jobs simultaneously.
- Workaround: Use `INSERT … ON CONFLICT DO NOTHING` (upsert) with a unique constraint.

---

## Performance Bottlenecks

**Correlation Matrix Computed on Every API Request:**
- Problem: `GET /api/correlation/matrix` and `GET /api/correlation/crisis` both call `correlation_engine.compute_correlation_matrix()` on every request. This loads price history for all BIST100 stocks from DB, builds a pandas DataFrame, and computes a full correlation matrix — a heavy operation.
- Files: `backend/app/services/dynamic_correlation.py:52`, `backend/app/api/endpoints.py:570-624`
- Cause: No result caching; the `last_computed` attribute exists on the class but is never used to short-circuit the computation.
- Improvement path: Cache the result in-memory with a TTL (e.g., 30 minutes) using `last_computed`; the attribute already exists but is unused.

**Sequential yfinance Calls for 100 Stocks:**
- Problem: `collect_price_data` and `initialize_stocks` call `yf.Ticker(symbol).history()` sequentially in a loop. yfinance supports `yf.download([...], threads=True)` for bulk downloads.
- Files: `backend/app/services/data_collector.py:103-105`, `backend/app/services/data_collector.py:44-92`
- Cause: Per-ticker API calls instead of bulk download.
- Improvement path: Use `yf.download(symbols_list, period=period, group_by="ticker", threads=True)` for a single batched API call.

**ML Prediction Blocks Event Loop:**
- Problem: `MLAnalysisEngine._train_and_predict` trains and runs XGBoost prediction synchronously (no `run_in_executor`). Numpy/sklearn operations block the asyncio event loop during `collect_ml_predictions` when called from an async background job.
- Files: `backend/app/services/ml.py:96-116`
- Cause: CPU-bound computation without executor offloading.
- Improvement path: Wrap with `await asyncio.get_event_loop().run_in_executor(None, train_fn, ...)`.

---

## Fragile Areas

**`causal_engine.run_realtime_scenarios()` Called in Portfolio Read Path:**
- Files: `backend/app/api/endpoints.py:107-111`
- Why fragile: The portfolio GET endpoint calls the causal engine and KAP parser inline on every request. Any failure in either service silently swallows the error (caught by broad `except Exception`) and returns no alerts — callers cannot distinguish "no alerts" from "service failed."
- Safe modification: Move scenario enrichment to a cached property or background-computed field; never call heavy analytical services inline in a read endpoint.
- Test coverage: No tests exist for this code path.

**`event_fusion._compute_event_impacts` Blindly Indexes `sources[0]`:**
- Files: `backend/app/services/event_fusion.py:318`
- Why fragile: `event.get("sources", [])[0]` raises `IndexError` if the event has no sources. This is inside a try/except that catches everything and returns `[]`, masking the real failure.
- Safe modification: Use `event.get("sources", ["Unknown"])[0]` or guard with a conditional.

**`ModelPortfolioHistory` Missing null-check Before Attribute Access:**
- Files: `backend/app/api/endpoints.py:218-228`
- Why fragile: After the fallback `generate_daily_model()` call, a second DB query may still return `None` (e.g., optimizer returned early due to < 3 candidates). Accessing `model.id` will raise `AttributeError` with a 500 response.
- Safe modification: Add `if not model: return {"current": None, "history": [...]}` with a 503 status.

---

## Scaling Limits

**In-Process APScheduler (No Distributed Coordination):**
- Current capacity: Works for a single process.
- Limit: Multiple uvicorn workers (`--workers N`) will each start their own `AsyncIOScheduler` instance, causing every scheduled job (KAP scan, event fusion, ML updates) to run N times simultaneously per interval.
- Scaling path: Use a database-backed job store (`apscheduler.jobstores.sqlalchemy`) or migrate to a proper task queue (Celery, ARQ, or Dramatiq) with a single worker process.

**No Result Pagination on Heavy Aggregation Queries:**
- Current capacity: Sector aggregation and full stock list queries load everything into memory and serialize to JSON.
- Limit: At 100 stocks this is acceptable, but if the stock universe is expanded, `GET /api/stocks` can load unbounded data.
- Scaling path: Offset/limit pagination is partially implemented but not enforced on all endpoints.

---

## Dependencies at Risk

**`yfinance` Scraping Dependency:**
- Risk: yfinance scrapes Yahoo Finance without an official API contract. Yahoo Finance has broken compatibility multiple times. Version `0.2.54` is pinned but upstream changes can cause silent data gaps or errors.
- Impact: All price data, fundamental data, and market data ingestion fails.
- Migration plan: Add a fallback to Borsa Istanbul's official data store (`datastore.borsaistanbul.com`) or a paid market data provider (Matriks, Finnet).

**`feedparser` Is an Optional Import but Critical for KAP:**
- Risk: `feedparser` is guarded with a `try/except ModuleNotFoundError` and falls back to mock data rather than raising. An environment where `feedparser` is missing will silently process fake KAP announcements.
- Impact: All sentiment scores, causal analysis, and risk alerts based on KAP are based on fake data.
- Migration plan: Make `feedparser` a hard dependency; fail fast at startup if absent.

---

## Missing Critical Features

**No Rate Limiting on External API Calls:**
- Problem: DeepSeek LLM API (`llm_sentiment.py`) is called for every KAP announcement that arrives. With KAP scanning every 5 minutes and potentially 50 announcements, this can exhaust token quotas or trigger rate limit errors from DeepSeek in bursts.
- Files: `backend/app/services/llm_sentiment.py`, `backend/app/services/kap_parser.py`
- Blocks: Production reliability of the LLM sentiment pipeline.

**No Input Validation on `PortfolioCreate.buy_date`:**
- Problem: `add_portfolio_item` silently ignores invalid `buy_date` strings (bare `except ValueError: pass` with no error returned to the caller).
- Files: `backend/app/api/endpoints.py:154-158`
- Blocks: Users cannot know if their date was accepted or silently dropped.

---

## Test Coverage Gaps

**No Tests Exist Anywhere:**
- What's not tested: The entire backend codebase has zero test files (`test_*.py` and `*_test.py` patterns return nothing). No unit tests, integration tests, or API contract tests.
- Files: `backend/app/` (entire directory)
- Risk: Any refactoring of scoring weights, causal engine, portfolio optimizer, or DB schema can break silently. The ML heuristic fallback, event fusion deduplication logic, and crisis mode detection in `DynamicCorrelationMatrix` are all completely untested.
- Priority: High — especially for `backend/app/services/scoring.py`, `backend/app/services/ml.py`, and `backend/app/api/endpoints.py`.

---

*Concerns audit: 2026-04-16*
