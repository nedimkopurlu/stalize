# Pitfalls Research

**Domain:** AI-powered financial analysis platform (BIST 100) — refactor + LLM chat addition
**Researched:** 2026-04-16
**Confidence:** HIGH (most pitfalls are directly evidenced in the existing codebase, confirmed by domain research)

---

## Critical Pitfalls

### Pitfall 1: Silent Mock Data in Production Data Pipelines

**What goes wrong:**
A service fails to load a dependency (e.g., `feedparser`), catches the `ImportError`, and substitutes synthetically generated fake data. Every downstream consumer — sentiment scoring, causal graph, ML features, LLM briefing context — then operates on fiction. The system looks healthy: no exceptions, no 500s, green logs. The AI's "daily briefing" is an analysis of invented KAP announcements.

**Why it happens:**
Developers add mock fallbacks during early development to keep the service runnable without the full environment configured. The guard is never removed or elevated to a startup-time hard failure.

**How to avoid:**
- At application startup (lifespan event in FastAPI), verify every critical dependency is importable and reachable. Raise `RuntimeError` if not — refuse to start.
- Never let a data source fall back to mocks in any code path that runs outside of an explicit `TEST_MODE` flag.
- `feedparser` must be a hard dependency in `requirements.txt`, not a guarded optional import.
- Add a startup health check endpoint that reports `{ "kap": "live" | "mock" | "down" }` so the status is visible.

**Warning signs:**
- KAP news items have suspiciously round timestamps or identical structure.
- Log lines show `_generate_mock_announcements` being called outside tests.
- All sentiment scores cluster near 0 / "nötr" despite market news days.

**Phase to address:** Data pipeline hardening phase (before any LLM feature build). This must be fixed before LLM chat can trust its context.

---

### Pitfall 2: LLM Receives Stale or Incomplete Context and Sounds Confident Anyway

**What goes wrong:**
The LLM (DeepSeek) is asked to produce a daily briefing or answer a chat question. The context passed in the prompt includes data that is hours or days old (because the scheduler missed a run, or yfinance rate-limited silently), or is structurally incomplete (indirect_impact = 0, scoring weights diverge from what the analysis actually used). The model produces a fluent, confident-sounding response that misrepresents market reality. There is no signal to the user that the data underlying the response is stale.

**Why it happens:**
LLMs don't know what they don't know. They generate plausible text from whatever context is provided. A prompt saying "EREGL kapanış: 48.20 TL (dün)" when today is three days later causes the model to reason from outdated prices as if they are current.

**How to avoid:**
- Every data object passed to the LLM prompt must carry an explicit `as_of` timestamp. The prompt template must include: "Bu veriler [tarih saat] itibarıyla geçerlidir."
- Before assembling the prompt, validate data freshness: price data must be < 24h old, KAP data < 6h old. If not, the LLM call must be blocked and the user must see a "veri güncel değil" warning rather than a stale answer.
- The daily briefing generation job must fail loudly (not silently skip) when source data is missing.
- Never include `indirect_impact` values in the LLM context until the knowledge graph propagation is implemented — passing a known-zero placeholder as if it is a real impact score directly misleads the model.

**Warning signs:**
- LLM briefing references yesterday's prices on a market-moving news day.
- Chat responses reference events that did not happen recently.
- `indirect_impact: 0` appears in every structured analysis the LLM receives.

**Phase to address:** LLM chat and briefing phase. Data validation layer must be built before the LLM prompt assembly layer.

---

### Pitfall 3: ML Model Trained on Every Request Blocks the Event Loop

**What goes wrong:**
`MLAnalysisEngine._train_and_predict` runs XGBoost `.fit()` synchronously inside an `async` function. This blocks the asyncio event loop for the duration of training (CPU-bound). When the background scheduler runs `collect_ml_predictions()` across 100 BIST stocks, the entire FastAPI process is blocked for minutes. Any concurrent HTTP request (including a user opening the dashboard) hangs until training completes. Adding an LLM streaming chat endpoint on top of this makes the problem immediately user-visible: the stream stalls mid-token.

**Why it happens:**
XGBoost training was written as synchronous code and wrapped in `async def` without `run_in_executor`. Python's asyncio does not preempt CPU-bound work.

**How to avoid:**
- Persist trained models to disk (joblib format with version metadata: `xgb_{symbol}_{YYYYMMDD}.joblib`). Load at prediction time; skip retraining if the persisted model is < 7 days old.
- When retraining IS needed (scheduled weekly), wrap the CPU-bound call: `await asyncio.get_event_loop().run_in_executor(None, train_fn, X, y)`.
- Keep model artifacts in `settings.ML_MODEL_DIR` with a metadata sidecar (`model_meta.json`) recording training date, feature list, and XGBoost version. This prevents loading a model trained against a different feature schema.
- Never retrain during a user-facing request. Retraining is a background scheduled task only.

**Warning signs:**
- Dashboard loads slowly right after a data collection cycle.
- LLM stream chunks arrive with irregular multi-second gaps.
- `asyncio` event loop lag warnings in logs.

**Phase to address:** ML persistence phase — must be completed before LLM streaming chat is added, because streaming latency is highly sensitive to event loop blocking.

---

### Pitfall 4: LLM API Called Unboundedly Per KAP Announcement (Token Quota Exhaustion)

**What goes wrong:**
KAP is scanned every 5 minutes. On active market days, 30-50 announcements can arrive in a single scan. `llm_sentiment.py` makes one DeepSeek API call per announcement — no rate limiting, no queuing, no deduplication check. A burst of 50 announcements triggers 50 concurrent async API calls. This either exhausts the daily token budget, triggers DeepSeek's server-side throttling (which causes silent failures that fall back to `sentiment_score: 0.0`), or both.

**Why it happens:**
The sentiment service was built for low-volume testing. The "call LLM per news item" pattern works fine in demos; it breaks in production on active trading days (IPO announcements, earnings season, central bank decisions).

**How to avoid:**
- Implement a priority queue for LLM sentiment calls. Process only announcements with `importance_score > threshold` immediately; batch lower-priority items.
- Add a concurrency limiter: use `asyncio.Semaphore(max_concurrent=5)` around DeepSeek calls.
- Cache sentiment results by announcement ID — if the same KAP announcement appears in two consecutive scans, do not call the LLM again.
- Track daily token spend in a simple counter. If the counter exceeds 80% of budget, switch to a cheap heuristic (keyword matching) for the remainder of the day and alert the operator.
- Use DeepSeek's off-peak pricing window (16:30–00:30 GMT) for non-urgent batches.

**Warning signs:**
- All sentiment results return `{"sentiment_score": 0.0, "sentiment_label": "nötr"}` on high-news days (silent error fallback in `llm_sentiment.py`).
- DeepSeek API dashboard shows spike in token usage followed by a gap.
- KAP scan logs show many `DeepSeek API Hatası` entries.

**Phase to address:** LLM integration hardening — before daily briefing goes live.

---

### Pitfall 5: LLM Streaming Response Errors After Headers Are Sent

**What goes wrong:**
In FastAPI SSE/streaming, once the response generator starts yielding, HTTP headers have already been sent with status 200. If the LLM API call fails midway through the stream (DeepSeek timeout, network drop, malformed chunk), the server cannot send an HTTP 500. The client sees a truncated stream with no error signal. The UI shows a half-rendered AI response and has no way to distinguish "streaming complete" from "stream died."

**Why it happens:**
Standard HTTP error handling (`raise HTTPException`) does not work after the generator has started. Developers assume try/except around the generator will propagate errors to the client — it does not.

**How to avoid:**
- Use a sentinel event pattern: always end the stream with a terminal event, either `data: [DONE]` on success or `data: {"error": "reason"}` on failure. The frontend must consume this sentinel and handle the error branch.
- Wrap the entire LLM generator in try/except. On exception, yield the error sentinel before returning.
- Set a per-request timeout on the DeepSeek call (e.g., 30s). If no chunk arrives within the timeout, yield the error sentinel and close cleanly.
- Never rely on context managers for stream resource cleanup — they execute before the response is sent. Use try/finally inside the async generator instead.

**Warning signs:**
- Frontend shows partial AI text that suddenly stops with no "done" signal.
- Users report the AI chat "freezing" intermittently.
- No error logged server-side but UI shows incomplete response.

**Phase to address:** LLM chat streaming phase — before any frontend integration.

---

### Pitfall 6: Scoring Weight Divergence Silently Corrupts All Recommendations

**What goes wrong:**
`config.py` defines ensemble weights (technical=0.20, fundamental=0.25, etc., summing to 0.90) that are never read by `ScoringEngine`. `ScoringEngine.BASE_WEIGHTS` hardcodes different values (technical=0.30, fundamental=0.20). When a developer adjusts weights in config expecting to tune scoring behavior, nothing changes. The LLM briefing's "buy/sell/hold" rationale references "weights" that do not match runtime behavior. Debugging why a particular stock is rated unexpectedly is extremely difficult.

**Why it happens:**
The scoring service was written independently of the config module. Both grew separately. No test caught the divergence because there are zero tests.

**How to avoid:**
- Remove weight constants from `config.py` entirely, OR make `ScoringEngine.__init__` read from `settings` and validate that weights sum to 1.0 at startup.
- Add a startup assertion: `assert abs(sum(settings.SCORE_WEIGHTS.values()) - 1.0) < 0.001`.
- The weight source of truth must be exactly one place. Choose `scoring.py` (closer to usage) and delete the `config.py` copies.

**Warning signs:**
- Changing `WEIGHT_TECHNICAL` in `.env` has no effect on stock rankings.
- Stock recommendations change unexpectedly after a config-only commit.
- Crisis mode weight override (`crisis_mode` logic in `_resolve_weights`) produces weights that also don't sum to 1.0 under all branches.

**Phase to address:** Scoring system refactor phase — early, before adding LLM chat that will narrate these scores.

---

### Pitfall 7: Monolithic endpoints.py Makes Refactoring Cascade into Breakage

**What goes wrong:**
All 38k characters of API surface are in one file. Adding a new chat router requires editing the same file that handles portfolio writes, stock data reads, macro scan triggers, and correlation endpoints. Any merge or refactor that touches endpoints.py risks breaking unrelated endpoints. The file is also untestable as a unit — you cannot import just the chat router for testing without loading the entire dependency graph.

**Why it happens:**
FastAPI makes it trivially easy to keep adding routes to `app`. The growth is invisible until the file is already unmaintainable.

**How to avoid:**
- Before adding any new feature (chat, briefing), split endpoints.py into domain routers first: `routers/stocks.py`, `routers/portfolio.py`, `routers/intelligence.py`, `routers/chat.py`, `routers/macro.py`.
- Each router is a separate `APIRouter` instance, included in `main.py` with a prefix.
- The chat router must be isolated from the beginning — it will have fundamentally different concerns (streaming, LLM state, conversation history) that do not belong in the same file as portfolio CRUD.
- Incremental split strategy: move one domain at a time, run the existing app after each move to verify no breakage.

**Warning signs:**
- Adding a chat endpoint requires scrolling past 1,000 lines of unrelated code.
- Two developers editing endpoints.py simultaneously causes merge conflicts on unrelated features.
- An import error in one endpoint breaks all endpoints.

**Phase to address:** Architectural refactor phase — must be the first structural change, before any feature addition.

---

### Pitfall 8: yfinance Silent Data Gaps Corrupt ML Features and LLM Briefing Context

**What goes wrong:**
yfinance is an unofficial scraper. Yahoo Finance has broken its API contract multiple times and rate-limits aggressively (429 errors). The current sequential per-ticker loop for 100 BIST stocks amplifies the rate-limit surface. When a 429 occurs, `yf.Ticker(symbol).history()` returns an empty DataFrame — not an exception. The empty DataFrame is silently stored (or skipped), leaving price history with gaps. ML features computed from gapped data produce meaningless predictions. The daily briefing LLM receives "no data" for a major stock and either hallucinates prices or omits the stock silently.

**Why it happens:**
Empty DataFrame is falsy in Python but doesn't raise. Developers check `if df is None` but not `if df.empty`.

**How to avoid:**
- Always check `if df.empty` after yfinance calls, not just `if df is None`. Log and alert on empty returns for actively tracked symbols.
- Use `yf.download(symbols_list, ..., threads=True)` for bulk fetching — one batched call vs. 100 sequential calls massively reduces rate-limit exposure.
- Add exponential backoff with jitter on 429 responses.
- Track per-symbol `last_successful_fetch` timestamp. If a symbol has not been updated in > 48h, mark it `data_stale=True` and exclude it from the LLM briefing context rather than including outdated values.
- Document a fallback: Borsa Istanbul's official `datastore.borsaistanbul.com` or a paid provider (Matriks/Finnet) for the most critical 30 symbols.

**Warning signs:**
- Some stocks consistently have `overall_score = 50.0` (the default when scores cannot be computed).
- Price history table has date gaps for specific symbols.
- yfinance logs show `YFRateLimitError` silently caught by broad `except Exception`.

**Phase to address:** Data pipeline hardening — alongside KAP fix, before LLM features.

---

### Pitfall 9: Conversation History Context Window Overflow in LLM Chat

**What goes wrong:**
A multi-turn chat session accumulates the full conversation history in each API call. After 15-20 exchanges about different stocks, the total token count exceeds DeepSeek's context window. The model either silently truncates early messages (losing crucial system context and data) or the API returns an error. In a financial context this is especially dangerous: the model may "forget" the investment philosophy, the risk profile constraints, or the data it was given about a specific stock at the start of the session.

**Why it happens:**
The naive pattern for multi-turn chat is to append every message to a growing list and send the entire list each time. This works in demos with short conversations.

**How to avoid:**
- Count tokens before each API call. DeepSeek's `deepseek-chat` context window is 64k tokens — enforce a hard cap at 50k (leaving headroom for the response).
- Use a sliding window strategy: always retain the system prompt + the most recent N exchanges + the data context block. Drop middle history when the window fills.
- For financial data context: structure prompts with a fixed "data block" prefix that DeepSeek's prompt caching can hit (cache hit = 90% cost reduction). Keep this prefix stable across turns; vary only the user question.
- Separate session state (conversation history) from request state (fresh market data) — rebuild the data context from DB on each turn, do not rely on earlier turns to carry current prices forward.

**Warning signs:**
- Chat responses become less accurate or more generic after long conversations.
- DeepSeek API returns token limit errors.
- Model references old prices that were mentioned earlier in the conversation rather than current data.

**Phase to address:** LLM chat phase — design conversation architecture before implementation.

---

### Pitfall 10: Datetime Timezone Inconsistency Corrupts Time-Filtered Queries

**What goes wrong:**
`data_collector.py` stores timestamps with `datetime.now()` (Turkey local time, UTC+3). Endpoints filter news and prices using `datetime.utcnow()`. On a server in Turkey's timezone, a KAP announcement stored at 14:00 local time appears to the query as if it arrived at 11:00 UTC — queries with `>= cutoff` miss recent items or include stale ones. The daily briefing job, which filters for "today's" announcements, silently excludes the most recent 3 hours of KAP data when running on a UTC+3 server.

**Why it happens:**
Python's `datetime.now()` vs `datetime.utcnow()` difference is easy to miss. The bug is latent until the server is deployed outside UTC.

**How to avoid:**
- Standardize on UTC-aware datetimes throughout: `datetime.now(timezone.utc)` everywhere. Never use naive `datetime.now()` or `datetime.utcnow()` — both are deprecated in Python 3.12+.
- Add a startup check: verify `datetime.now(timezone.utc).utcoffset() == timedelta(0)` or set `TZ=UTC` in the environment.
- Add a database migration to add timezone awareness to `published_at`, `created_at` columns.
- This fix must precede any LLM feature that reasons about "today's" data — briefing generation is entirely time-sensitive.

**Warning signs:**
- "Today's" briefing is missing the last 3 hours of KAP news.
- News items appear out of order in the event timeline.
- Correlation between `datetime.now()` and `datetime.utcnow()` usages produces inconsistent "freshness" checks.

**Phase to address:** Data pipeline hardening — alongside mock data fix.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Mock data fallback on import error | Service stays "running" with no deps | Silent data corruption in production | Never in production code paths — only behind explicit `TEST_MODE` flag |
| Train XGBoost per-request | No disk I/O setup needed | Event loop blocked, 100x slower than needed | Never — joblib persistence is < 20 lines of code |
| All routes in one endpoints.py | No file organization overhead | Any refactor risks breaking unrelated endpoints; untestable | Never past prototype stage |
| `except Exception: return mock_value` broad catches | No crashes visible | Real errors hidden, debugging impossible | Never without at minimum logging `traceback.format_exc()` |
| `datetime.now()` naive timestamps | Simpler code | Silent timezone bugs on any non-UTC server | Only for purely local, display-only timestamps — never for stored/compared values |
| LLM call per KAP announcement with no queue | Simple linear code | Token quota exhaustion on busy days | Never in production — even a basic semaphore is mandatory |
| Hardcoded scoring weights in two places | Flexibility to tune each independently | Weights diverge silently; config has no effect | Never — single source of truth is mandatory |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| DeepSeek API (openai SDK) | Assuming JSON output is always valid — model occasionally leaks markdown fences | Always strip fences AND wrap `json.loads` in try/except with structured fallback, never return raw text to downstream |
| DeepSeek streaming | Using `response.choices[0].message.content` (blocks until complete) | Use `stream=True` with `async for chunk in response` — blocking defeats the purpose of streaming |
| yfinance bulk download | Calling `yf.Ticker(symbol).history()` in a loop | Use `yf.download(symbols, threads=True)` — one HTTP session, 10-50x fewer rate limit events |
| SQLAlchemy async session | Calling `db.commit()` inside a GET endpoint read path | Separate reads from writes — GET endpoints must never commit; use scheduled jobs for persistence |
| APScheduler with multiple uvicorn workers | Each worker starts its own scheduler → N×jobs run simultaneously | Use `workers=1` for the scheduler process, or use SQLAlchemy jobstore for distributed coordination |
| XGBoost joblib persistence | Using `pickle.dump` — breaks across XGBoost versions | Use `model.save_model("model.json")` (XGBoost native) for cross-version safety, or joblib with version metadata sidecar |
| FastAPI SSE streaming | Raising `HTTPException` inside a started generator | Cannot change HTTP status after headers are sent — use error sentinel events (`data: {"error": "..."}`) |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| N+1 price history queries (125,000 SELECTs on full load) | Initial data load takes hours; DB CPU pegged | Bulk-fetch existing dates per stock, filter in Python, then bulk insert | Immediately on first `full_initial_load` with real data |
| Correlation matrix computed on every API request | `/api/correlation/matrix` takes 5-30s; blocks other requests | Cache result in-memory with 30-min TTL using the `last_computed` attribute that already exists but is unused | From the very first real user hit |
| Sequential yfinance calls for 100 symbols | Data collection cycle takes 10-20 minutes | Use `yf.download(symbols_list, threads=True)` for a single batched request | Immediately on any full refresh |
| CPU-bound XGBoost training in async function | All HTTP requests stall during scheduled data collection | `run_in_executor` for training, or persist and load instead of retraining | Every scheduled collection run |
| `GET /api/portfolio` committing to DB on every read | Portfolio endpoint causes write lock contention; cannot be cached | Separate price refresh from portfolio read; only persist on schedule | Under any moderate load or caching attempt |
| LLM full conversation history in every API call | Long sessions hit token limits; costs grow with session length | Sliding window with fixed system prompt prefix for cache hits | After ~15 turns in a conversation |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| CORS wildcard (`allow_origins=["*"]`) in production | Any website can call the API including portfolio write endpoints | Set `CORS_ORIGINS` from `settings` at startup; the config already has a proper list — use it |
| Unsanitized `sort_by` parameter passed to `getattr(Stock, sort_by)` | Attribute name enumeration via error messages; SQL injection surface | Whitelist: `assert sort_by in {"overall_score", "technical_score", "fundamental_score"}` |
| No rate limiting on LLM endpoints | A single curl loop can exhaust daily token budget | Add per-IP or per-session rate limiting on chat and briefing endpoints |
| LLM receives raw user input with no sanitization | Prompt injection: user can instruct the model to ignore investment constraints, reveal system prompt, or produce harmful financial advice | Separate system context from user input structurally; validate that user message is a question about a known stock or topic before forwarding to LLM |
| `DEBUG=True` default logs every SQL statement | Credential and query leakage in any non-dev deployment | Change default to `False`; require explicit `DEBUG=true` in `.env` to enable |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| LLM briefing shows "no data" or generic text without explaining why | User cannot tell if the AI is analyzing real data or has nothing to work with | Show explicit data freshness badge: "KAP: 4 dakika önce | Fiyat: 23 dakika önce" next to every AI output |
| LLM chat response streams then abruptly stops with no error | User assumes the AI is "thinking" and waits indefinitely | Terminal sentinel event on every stream end (success or error); frontend shows "Yanıt tamamlandı" or "Hata oluştu" |
| Recommendation ("AL/SAT/TUT") changes between page loads without data changing | User loses trust in the AI | Scores should only update when a scheduled job runs, not on every request; show "Son güncelleme: HH:MM" |
| All 100 BIST stocks shown in the briefing | Overwhelming; user cannot act on 100 items | AI briefing must surface only top 5-7 highest-signal stocks, with a clear ranking rationale |
| Scoring weights are opaque — user cannot understand why a stock is rated 73 | User cannot validate or trust the score | Show score breakdown: "Teknik: 82 (×0.30) + Temel: 65 (×0.20) + ..." in the UI |

---

## "Looks Done But Isn't" Checklist

- [ ] **KAP parser:** Verify `feedparser` is in `requirements.txt` as a hard dep AND mock path is unreachable except in tests — confirm with `grep -r "_generate_mock" backend/` returns no calls from non-test code
- [ ] **ML persistence:** Verify model is loaded from disk, not retrained — confirm with timestamp on `*.joblib` file and log line "Model yüklendi" not "Model eğitildi" on a non-retraining day
- [ ] **Scoring weights:** Verify `config.py` weight constants are either deleted or are the sole source used by `ScoringEngine` — confirm with `sum(weights.values()) == 1.0` assertion at startup
- [ ] **LLM streaming:** Verify every stream path ends with an explicit sentinel — confirm by disconnecting the client mid-stream and checking server logs show clean generator exit, not exception
- [ ] **Timezone handling:** Verify all stored timestamps are UTC-aware — confirm with `SELECT published_at AT TIME ZONE 'UTC' FROM news_items LIMIT 5` returning consistent values
- [ ] **Daily briefing data freshness:** Verify briefing refuses to generate (or shows a warning) when price data is > 24h old — confirm by stopping the data collector and requesting a briefing
- [ ] **LLM context includes `as_of` timestamps:** Verify system prompt or data block always includes the data snapshot date — confirm by reading a generated prompt in debug logs
- [ ] **Event fusion indirect_impact:** Verify no endpoint returns `indirect_impact: 0` as a meaningful value to the LLM — either implement it or exclude the field from LLM context

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Mock KAP data served to LLM for extended period | HIGH | Identify affected time range from logs; re-run KAP scan with live feedparser; retrain ML models with corrected data; invalidate cached briefings |
| Token quota exhausted mid-day | LOW | Add rate limiter with hard cap; implement fallback to heuristic sentiment for remainder of day; request quota increase from DeepSeek |
| ML models trained on wrong feature schema after schema change | MEDIUM | Delete all `.joblib` files in `ML_MODEL_DIR`; force full retrain in off-peak executor; verify feature names in sidecar metadata match current `_prepare_features` output |
| Scoring weights diverged for unknown duration | MEDIUM | Audit git history for when the divergence started; recompute `overall_score` for all stocks; surface change in changelog for user awareness |
| Endpoints.py refactoring breaks live routes | MEDIUM | Maintain a route compatibility test that hits every endpoint with a minimal valid request; run before and after each router extraction |
| LLM chat conversation history lost on server restart | LOW | This is acceptable for a personal tool — document that sessions are not persistent; optionally persist conversation history to a `chat_sessions` DB table |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Silent mock data in production | Phase 1: Data pipeline hardening | `grep -r "mock" backend/app/services/` returns zero production code paths |
| Stale LLM context without timestamps | Phase 3: LLM prompt architecture | Every assembled prompt logged in debug contains `as_of` field |
| ML blocking event loop | Phase 2: ML persistence + async fix | `asyncio` event loop lag < 100ms during scheduled collection |
| LLM API unbounded calls | Phase 3: LLM integration hardening | Token spend tracker shows cap enforcement on a simulated burst test |
| SSE stream errors undetectable by client | Phase 4: Chat streaming implementation | Frontend test: disconnect DeepSeek mid-stream → UI shows error message, not frozen spinner |
| Scoring weight divergence | Phase 1: Scoring system unification | Single grep confirms weights defined in exactly one place; startup assertion passes |
| Monolithic endpoints.py | Phase 1: Architectural refactor | File count in `routers/` ≥ 5; `endpoints.py` deleted or < 100 lines |
| yfinance silent data gaps | Phase 1: Data pipeline hardening | `data_stale` flag visible in stock model; briefing excludes stale stocks |
| Context window overflow | Phase 4: Chat design | 50-turn stress test stays under 50k tokens per request |
| Datetime timezone bugs | Phase 1: Data pipeline hardening | All `datetime.now()` occurrences replaced; startup TZ assertion passes |

---

## Sources

- CONCERNS.md (codebase audit, 2026-04-16) — direct evidence for pitfalls 1, 2, 3, 4, 6, 7, 8, 10
- [OWASP LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) — pitfall 5, security section
- [FINOS AI Governance: Hallucination and Inaccurate Outputs](https://air-governance-framework.finos.org/risks/ri-4_hallucination-and-inaccurate-outputs.html) — pitfall 2
- [DeepSeek API Rate Limit Documentation](https://api-docs.deepseek.com/quick_start/rate_limit) — pitfall 4
- [FastAPI Issue #1936: Context managers with StreamingResponse](https://github.com/fastapi/fastapi/issues/1936) — pitfall 5
- [FastAPI SSE Discussion #15129: Errors before stream starts](https://github.com/fastapi/fastapi/discussions/15129) — pitfall 5
- [XGBoost Model Persistence — Official Docs](https://xgboost.readthedocs.io/en/latest/tutorials/saving_model.html) — pitfall 3
- [yfinance Rate Limit Issues #2289](https://github.com/ranaroussi/yfinance/issues/2289) — pitfall 8
- [LLM Caching Guide — Latitude](https://latitude.so/blog/ultimate-guide-to-llm-caching-for-low-latency-ai) — pitfall 9
- [FastAPI Best Practices — zhanymkanov](https://github.com/zhanymkanov/fastapi-best-practices) — pitfall 7, integration gotchas
- [8 LLM Production Challenges — Shift Asia](https://shiftasia.com/community/8-llm-production-challenges-problems-solutions/) — pitfall 2, 9

---
*Pitfalls research for: BIST 100 AI investment advisor (Stalize) — refactor + LLM chat*
*Researched: 2026-04-16*
