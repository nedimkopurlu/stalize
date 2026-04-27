# Phase 1: Foundation Repair - Research

**Researched:** 2026-04-16
**Domain:** Python/FastAPI backend surgery — mock removal, weight wiring, dependency pruning, router refactoring, UTC datetime standardization
**Confidence:** HIGH (all findings grounded in direct codebase inspection)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**KAP Failure Mode (FOND-01)**
- D-01: If `feedparser` is not installed, the backend fails at startup with a clear `RuntimeError` — feedparser is treated as a required dependency, not optional
- D-02: If feedparser IS installed but KAP RSS is temporarily unreachable (network error, malformed feed, timeout) → return an empty list + write a `WARNING` log. The scheduler continues running and will retry on the next interval.
- D-03: `_generate_mock_announcements()` is completely deleted — no mock path should be reachable from production code. All three fallback paths (lines 66-68, 103, 110 in kap_parser.py) are removed.

**Scoring Weights (FOND-02)**
- D-04: `config.py` values win. The authoritative weights are:
  - `WEIGHT_TECHNICAL = 0.20`
  - `WEIGHT_FUNDAMENTAL = 0.25`
  - `WEIGHT_ML = 0.20`
  - `WEIGHT_SENTIMENT = 0.10`
  - `WEIGHT_CAUSAL = 0.15`
  - `WEIGHT_MACRO = 0.10`
- D-05: `WEIGHT_MACRO` maps to `Stock.macro_score` column — if the column exists and has a value, include it in the weighted sum; if null/missing, treat as 0 (neutral contribution)
- D-06: `scoring.py` `BASE_WEIGHTS` class constant is removed entirely. `ScoringEngine` reads all weights from `settings` (the pydantic-settings singleton) at runtime. Changing a weight in config.py (or .env) is immediately reflected — zero code changes elsewhere required.

**Router Structure (FOND-04)**
- D-07: Domain-based file split into 6 router files inside `backend/app/api/`:
  - `stocks.py` — stock list, stock detail, rankings, scoring endpoints
  - `macro.py` — TCMB, TUIK, macro indicators, FX/commodity data
  - `portfolio.py` — user portfolio and model portfolio endpoints
  - `intelligence.py` — market intelligence, event fusion, correlation
  - `causal.py` — causal chain analysis endpoints
  - `admin.py` — health check, manual scan triggers
- D-08: `endpoints.py` is deleted entirely after all content is moved to domain routers
- D-09: `main.py` uses one `app.include_router(x.router, prefix="/api")` call per domain router — no aggregator __init__.py

**Unused Dependencies (FOND-03)**
- D-10: Remove from `requirements.txt`: `tensorflow`, `torch`, `transformers`, `sentencepiece` — all confirmed unused in codebase (STACK.md audit)
- D-11: Verify `vaderSentiment` usage before removing — it appears in `macro_news.py`; keep if used

**UTC Timestamps (FOND-05)**
- D-12: `model_portfolio.py` is the primary offender — `DateTime` → `DateTime(timezone=True)` and `datetime.utcnow` → `func.now()`. Fix inline using SQLAlchemy's existing pattern (matching all other models).
- D-13: Scan all service layer files for `datetime.utcnow()` or `datetime.now()` used in DB writes and replace with `datetime.now(timezone.utc)` from Python's `datetime` module.
- D-14: No Alembic migration needed for this phase — the existing `Base.metadata.create_all()` lifespan hook handles table updates on restart.

### Claude's Discretion
- How to organize the health check endpoint (in admin.py or keep as a standalone route)
- Whether `macro_news.py` endpoints go in `macro.py` or `intelligence.py`
- Exact log message wording for KAP WARNING events

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FOND-01 | KAP parser mock fallback kaldırılsın; feedparser yoksa startup'ta hata fırlatsın | kap_parser.py lines 16-19, 66-68, 103, 110 fully mapped; lifespan hook in main.py is the right place for startup check |
| FOND-02 | Scoring ağırlıkları tek yerden yönetilsin — config.py değerleri scoring.py BASE_WEIGHTS'e aktarılsın | scoring.py lines 22-28 and config.py lines 53-58 both mapped; macro_score column confirmed absent from stock.py |
| FOND-03 | tensorflow, torch, transformers, sentencepiece kaldırılsın (kullanılmıyor, 3-4GB boşa) | All 4 packages confirmed absent from backend/app/ imports; vaderSentiment confirmed used in macro_news.py — keep it |
| FOND-04 | endpoints.py domain router'lara bölünsün | All 31 endpoints enumerated and domain-assigned; import graph documented; 6 router files specified |
| FOND-05 | UTC/naive datetime karışıklığı giderilsin — tüm DB kayıtları UTC timezone-aware | model_portfolio.py is primary offender; additional datetime.utcnow() calls found in kap_parser.py and endpoints.py |
</phase_requirements>

---

## Summary

This phase is purely surgical backend repair — five independent defects that each corrupt data silently. No new features are introduced. All five changes are self-contained: none depends on the others, so they can be implemented and committed as separate tasks within the same phase.

The codebase is in a readable state. All existing models except `model_portfolio.py` already use the correct `DateTime(timezone=True)` + `func.now()` pattern. The pydantic-settings `Settings` class already has all the correct weight values defined — the problem is purely that `scoring.py` ignores them. The `feedparser` import is already guarded, but the guard routes to a mock instead of raising. These are all one-to-three line fixes per defect.

The largest work item is the router split (FOND-04): 31 endpoints across ~933 lines of `endpoints.py` must be sorted into 6 files and re-wired in `main.py`. There are no shared state dependencies between routers that would make this hard — every endpoint opens its own `AsyncSessionLocal()` session inline, so there is no global session object to thread across files.

**Primary recommendation:** Fix in this order — FOND-03 (zero risk, instant win), FOND-05 (model file change + grep scan), FOND-02 (scoring.py constant swap), FOND-01 (kap_parser.py surgery + main.py startup check), FOND-04 (router split last, largest change). Each task is independently committable.

---

## Standard Stack

### Core (already installed — no new packages needed for this phase)

| Library | Version | Purpose | Role in This Phase |
|---------|---------|---------|-------------------|
| fastapi | 0.115.12 | REST API framework | Router files use `APIRouter()` from fastapi |
| pydantic-settings | 2.8.1 | Settings from env | `settings` singleton is the target for weight reads |
| sqlalchemy[asyncio] | 2.0.40 | Async ORM | `DateTime(timezone=True)` + `func.now()` pattern |
| feedparser | 6.0.11 | RSS parsing | Must be promoted to a hard dependency (not try/except) |

### Packages to REMOVE

| Package | Version in requirements.txt | Evidence of Use | Action |
|---------|--------------------------|-----------------|--------|
| tensorflow | 2.19.0 | No import anywhere in `backend/app/` | DELETE |
| torch | 2.6.0 | No import anywhere in `backend/app/` | DELETE |
| transformers | 4.51.3 | No import anywhere in `backend/app/` | DELETE |
| sentencepiece | 0.2.0 | No import anywhere in `backend/app/` | DELETE |
| vaderSentiment | (no pin) | `from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer` in `macro_news.py` line 3 | KEEP |

**Note:** `vaderSentiment` has no version pin in `requirements.txt` — it is currently pulled as a transitive dependency. After removing `transformers`, verify it stays installed. If not, add an explicit line `vaderSentiment` to `requirements.txt`.

**Installation (after cleanup):**
```bash
cd backend
pip install -r requirements.txt
```

---

## Architecture Patterns

### Recommended Project Structure After FOND-04

```
backend/app/api/
├── stocks.py        # GET /stocks, GET /stocks/{symbol}, GET /stocks/{symbol}/prices,
│                    # GET /stocks/{symbol}/technical, POST /analysis/technical/run,
│                    # GET /rankings, GET /sectors, POST /scoring/update
├── macro.py         # POST /macro/tcmb/scan, POST /macro/tuik/scan, GET /macro/events
├── portfolio.py     # GET /portfolio, POST /portfolio, DELETE /portfolio/{item_id},
│                    # GET /model-portfolio
├── intelligence.py  # GET /intelligence/overview, GET /intelligence/fusion,
│                    # GET /intelligence/impact-ranking, GET /correlation/matrix,
│                    # GET /correlation/crisis, GET /correlation/diversification-advice,
│                    # GET /correlation/low-correlation-pairs
├── causal.py        # GET /causal/feed, GET /causal/scenarios, GET /causal/scenario,
│                    # GET /causal/triggers, GET /causal/stock/{symbol},
│                    # POST /causal/run-all
└── admin.py         # GET /health, POST /kap/scan, GET /dashboard
```

**Discretion recommendation:** Place `GET /health` and `GET /dashboard` in `admin.py`. The health endpoint and dashboard summary are operational concerns, not domain data. Place `POST /kap/scan` in `admin.py` as a manual trigger. Place `macro_news.py` endpoints (if any exist as endpoints) in `macro.py` — they are data source endpoints, not intelligence synthesis.

### Pattern 1: FastAPI Domain Router File

Every new router file follows this structure:
```python
# backend/app/api/stocks.py
import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from app.core.database import AsyncSessionLocal
from app.models.stock import Stock
# ... other model imports as needed

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/stocks")
async def get_stocks(...):
    ...
```

### Pattern 2: main.py Router Registration

Replace the single `app.include_router(router, prefix="/api")` call (line 159) with:
```python
from app.api import stocks, macro, portfolio, intelligence, causal, admin

app.include_router(stocks.router, prefix="/api")
app.include_router(macro.router, prefix="/api")
app.include_router(portfolio.router, prefix="/api")
app.include_router(intelligence.router, prefix="/api")
app.include_router(causal.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
```

Remove the old import: `from app.api.endpoints import router`

### Pattern 3: Settings-Driven Weights in ScoringEngine

Current broken pattern (scoring.py lines 22-28):
```python
BASE_WEIGHTS = {
    "technical_score": 0.30,    # WRONG — ignored config.py
    "fundamental_score": 0.20,
    ...
}
```

Correct pattern after fix:
```python
# No BASE_WEIGHTS class constant.

def _resolve_weights(self, stock: Stock) -> Dict[str, float]:
    from app.core.config import settings
    weights = {
        "technical_score": settings.WEIGHT_TECHNICAL,
        "fundamental_score": settings.WEIGHT_FUNDAMENTAL,
        "ml_score": settings.WEIGHT_ML,
        "sentiment_score": settings.WEIGHT_SENTIMENT,
        "causal_score": settings.WEIGHT_CAUSAL,
        "macro_score": settings.WEIGHT_MACRO,
    }
    # Crisis mode override retains same key names but different magnitudes
    sentiment = stock.sentiment_score if stock.sentiment_score is not None else self.DEFAULT_SCORE
    causal = stock.causal_score if stock.causal_score is not None else self.DEFAULT_SCORE
    crisis_mode = abs(sentiment - 50.0) >= 20.0 or abs(causal - 50.0) >= 25.0
    if crisis_mode:
        weights = {
            "technical_score": 0.20,
            "fundamental_score": 0.15,
            "sentiment_score": 0.30,
            "causal_score": 0.25,
            "ml_score": 0.10,
            "macro_score": 0.0,  # macro de-weighted in crisis
        }
    return weights
```

**CRITICAL detail:** `calculate_overall_score()` currently reads scores from a dict keyed by `"technical_score"`, `"fundamental_score"` etc. matching Stock attribute names. After adding `macro_score` to the weights dict, the scores dict in `calculate_overall_score` must also include it:
```python
scores = {
    "technical_score": stock.technical_score,
    "fundamental_score": stock.fundamental_score,
    "sentiment_score": stock.sentiment_score,
    "causal_score": stock.causal_score,
    "ml_score": stock.ml_score,
    "macro_score": getattr(stock, "macro_score", None),  # column does not yet exist
}
```
Because `macro_score` column does not exist in `Stock` yet (confirmed — not in `stock.py`), use `getattr(stock, "macro_score", None)` to safely return `None`. The existing normalization logic already handles `None` values by skipping them with zero weight contribution — this is the correct behavior per D-05.

### Pattern 4: feedparser Startup Guard

In `backend/app/main.py`, inside the `lifespan` function, before `scheduler.start()`:
```python
try:
    import feedparser  # noqa: F401
except ModuleNotFoundError:
    raise RuntimeError(
        "feedparser is not installed. "
        "Install it with: pip install feedparser==6.0.11"
    )
```

In `backend/app/services/kap_parser.py`, remove the `try/except ModuleNotFoundError` guard at the top and import feedparser directly:
```python
import feedparser  # hard import — fails loudly at module load if missing
```

The `fetch_latest_announcements` method body changes:
- Remove lines 66-68 (feedparser is None check → mock call)
- Remove lines 101-103 (empty announcements → mock call)
- Replace line 109-110 (except block → mock call) with `return []` and a WARNING log
- Delete the entire `_generate_mock_announcements` method

### Pattern 5: UTC Datetime Fix

**model_portfolio.py** — two columns need fixing:
```python
# Before (broken):
from datetime import datetime
generation_date = Column(DateTime, default=datetime.utcnow, index=True)
target_date = Column(DateTime, index=True)

# After (correct):
from sqlalchemy.sql import func
generation_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
target_date = Column(DateTime(timezone=True), index=True)
```

**Service layer files** — replace `datetime.utcnow()` in DB-write paths:
- `kap_parser.py` line 200: `datetime.utcnow()` in `published_at=` → `datetime.now(timezone.utc)`
- `kap_parser.py` line 290: `stock.last_data_update = datetime.utcnow()` → `datetime.now(timezone.utc)`
- `endpoints.py` (multiple): `datetime.utcnow().isoformat()` in JSON responses — these are cosmetic, not DB writes; lower priority but should be cleaned

Import pattern for all service files:
```python
from datetime import datetime, timezone
# Usage:
datetime.now(timezone.utc)
```

### Anti-Patterns to Avoid

- **Import feedparser conditionally:** The entire point of D-01 is to remove the conditional import. Never re-add `try/except ModuleNotFoundError` around feedparser.
- **Leaving BASE_WEIGHTS as a fallback:** Do not leave BASE_WEIGHTS in place and add a settings read on top. Remove the constant entirely — it will cause confusion if it survives.
- **Using `datetime.utcnow()` in new code:** Python 3.12 deprecated `utcnow()`; use `datetime.now(timezone.utc)` always. The existing `func.now()` in SQLAlchemy server defaults is correct and should not be replaced with Python-side defaults.
- **Aggregator `__init__.py` for routers:** D-09 explicitly forbids an `api/__init__.py` that re-exports all routers. Import each router module directly in `main.py`.
- **One mega import block in each new router:** Only import what each router actually uses. Copy only the imports needed by the endpoints moving into that file.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Settings singleton | Custom config loader | `pydantic-settings` `Settings` already in `config.py` | It's already there — `settings` object is imported everywhere |
| UTC-aware defaults in SQLAlchemy | Python `default=` lambda | `server_default=func.now()` with `DateTime(timezone=True)` | Server-side default is timezone-correct regardless of app server TZ; already the pattern in all other models |
| Feedparser absence detection | Custom import checker | Hard `import feedparser` at module top + RuntimeError in lifespan | Standard Python: direct imports raise ImportError/ModuleNotFoundError by default; check once at startup |
| Weight normalization | Custom math | Existing `weighted_sum / total_weight` logic in `calculate_overall_score` | Already handles missing scores correctly via the `total_weight` denominator |

**Key insight:** Every tool needed for this phase is already in the codebase. The work is removal and rewiring, not addition.

---

## Common Pitfalls

### Pitfall 1: macro_score Column Does Not Exist Yet

**What goes wrong:** D-05 says `WEIGHT_MACRO` maps to `Stock.macro_score` column. But `stock.py` has no `macro_score` column. Accessing `stock.macro_score` raises `AttributeError`.
**Why it happens:** The config has the weight defined but the DB column was never added.
**How to avoid:** Use `getattr(stock, "macro_score", None)` in `calculate_overall_score`. The `None` value is handled correctly by the existing weight normalization — it is simply skipped. Do NOT add the column in this phase (out of scope). Do NOT raise an error.
**Warning signs:** `AttributeError: 'Stock' object has no attribute 'macro_score'` in score calculation logs.

### Pitfall 2: Crisis Mode Weight Keys Must Match

**What goes wrong:** After adding `macro_score` to the normal-mode weights dict, the crisis-mode override dict must also include all the same keys (even if with weight 0). If crisis mode returns a dict without `macro_score`, the score loop will not process it, but the calling code assumes keys are consistent.
**Why it happens:** Two separate weight dicts defined in `_resolve_weights`.
**How to avoid:** Always define both weight dicts with the same set of keys. Use `macro_score: 0.0` in crisis mode (macro data is unreliable in crisis conditions anyway).

### Pitfall 3: Router File Circular Imports

**What goes wrong:** New router files import from `app.api.endpoints` (the old file) or from each other, creating circular imports.
**Why it happens:** The existing `endpoints.py` has some lazy imports inside endpoint functions (`from app.services.xxx import ...`). When moving these to new files, it is tempting to import at the top level, which can create cycles if the service imports from the API layer.
**How to avoid:** Keep the lazy `from ... import ...` inside endpoint function bodies where they appear now, OR move them to module-level only after confirming there is no cycle. The existing services do not import from `app.api`, so top-level imports in the new router files are safe.
**Warning signs:** `ImportError: cannot import name 'X' from partially initialized module` at startup.

### Pitfall 4: Weights Do Not Sum to 1.0 (Normal Mode)

**What goes wrong:** config.py weights: technical=0.20 + fundamental=0.25 + ml=0.20 + sentiment=0.10 + causal=0.15 + macro=0.10 = **1.00**. If a developer adds or changes a weight and the sum drifts from 1.0, the overall score is implicitly renormalized by `weighted_sum / total_weight` — but only when all scores are present. With missing scores, the renormalization produces different results than intended.
**Why it happens:** Weights defined as independent floats with no enforcement.
**How to avoid:** Add an assertion at startup or in the Settings validator: `assert abs(sum([WEIGHT_TECHNICAL, WEIGHT_FUNDAMENTAL, WEIGHT_ML, WEIGHT_SENTIMENT, WEIGHT_CAUSAL, WEIGHT_MACRO]) - 1.0) < 1e-6`. (This is a future-proofing note — not required for this phase, but worth adding.)

### Pitfall 5: datetime.utcnow in JSON Responses vs DB Writes

**What goes wrong:** Many `datetime.utcnow().isoformat()` calls appear in endpoints.py response dicts (e.g., `"timestamp": datetime.utcnow().isoformat()`). These are not DB writes — they are response formatting. Changing them to `datetime.now(timezone.utc).isoformat()` changes the output string format from `2026-04-16T10:00:00` to `2026-04-16T10:00:00+00:00`.
**Why it happens:** `utcnow()` returns naive datetime; `now(timezone.utc)` returns aware datetime with `+00:00` suffix.
**How to avoid:** The frontend must be able to parse either format. ISO 8601 allows both. If the frontend uses `new Date(str)` in JS, both formats parse correctly. Change these in the router migration but do not treat as a breaking change. If in doubt about the frontend, leave response-only calls as-is and only fix the DB write paths.

### Pitfall 6: feedparser Import Removal Breaks Existing Module-Level Code

**What goes wrong:** After removing the `try/except` guard from `kap_parser.py` and importing feedparser directly, the module fails to import if feedparser is not installed — even before the startup check in `lifespan` runs.
**Why it happens:** Python imports all modules at startup before `lifespan` executes.
**How to avoid:** This is the correct behavior per D-01. The startup check in `lifespan` is belt-and-suspenders documentation — the actual protection comes from the direct import failing at module load. Document this clearly in the commit message.

---

## Code Examples

### Confirmed Working Pattern: SQLAlchemy Timezone-Aware Column (from stock.py)

```python
# Source: backend/app/models/stock.py lines 41-43
from sqlalchemy.sql import func

created_at = Column(DateTime(timezone=True), server_default=func.now())
updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
last_data_update = Column(DateTime(timezone=True), nullable=True)
```

Apply exactly this pattern to `model_portfolio.py` `generation_date` and `target_date`.

### Confirmed Working Pattern: FastAPI APIRouter (from endpoints.py lines 25-26)

```python
# Source: backend/app/api/endpoints.py lines 9, 25-26
from fastapi import APIRouter
router = APIRouter()
```

Same pattern in every new domain router file.

### Settings Singleton Import

```python
# Source: backend/app/services/kap_parser.py line 22
from app.core.config import settings
# Then access: settings.WEIGHT_TECHNICAL etc.
```

### Endpoint-Level Lazy Import Pattern (preserve this in migrated routers)

```python
# Source: backend/app/api/endpoints.py line 459
@router.post("/macro/tcmb/scan")
async def trigger_tcmb_scan():
    from app.services.tcmb_adapter import run_tcmb_scan  # lazy import OK
    stored = await run_tcmb_scan()
    ...
```

---

## Endpoint Domain Assignment (Complete Map)

The 31 endpoints in `endpoints.py` map to routers as follows:

| Endpoint | Method | Target Router |
|----------|--------|--------------|
| `/portfolio` | GET | portfolio.py |
| `/portfolio` | POST | portfolio.py |
| `/portfolio/{item_id}` | DELETE | portfolio.py |
| `/model-portfolio` | GET | portfolio.py |
| `/dashboard` | GET | admin.py |
| `/stocks` | GET | stocks.py |
| `/stocks/{symbol}` | GET | stocks.py |
| `/stocks/{symbol}/prices` | GET | stocks.py |
| `/stocks/{symbol}/technical` | GET | stocks.py |
| `/analysis/technical/run` | POST | stocks.py |
| `/rankings` | GET | stocks.py |
| `/sectors` | GET | stocks.py |
| `/scoring/update` | POST | stocks.py |
| `/causal/feed` | GET | causal.py |
| `/causal/scenarios` | GET | causal.py |
| `/causal/scenario` | GET | causal.py |
| `/causal/triggers` | GET | causal.py |
| `/causal/stock/{symbol}` | GET | causal.py |
| `/causal/run-all` | POST | causal.py |
| `/kap/scan` | POST | admin.py |
| `/macro/tcmb/scan` | POST | macro.py |
| `/macro/tuik/scan` | POST | macro.py |
| `/macro/events` | GET | macro.py |
| `/intelligence/overview` | GET | intelligence.py |
| `/intelligence/fusion` | GET | intelligence.py |
| `/intelligence/impact-ranking` | GET | intelligence.py |
| `/correlation/matrix` | GET | intelligence.py |
| `/correlation/crisis` | GET | intelligence.py |
| `/correlation/diversification-advice` | GET | intelligence.py |
| `/correlation/low-correlation-pairs` | GET | intelligence.py |
| `/health` | GET | admin.py |

**Count verification:** 31 endpoints listed. Matches context assertion.

**Imports needed per router (module-level):**

- `stocks.py`: `Stock`, `PriceHistory`, `technical_engine`, `scoring_engine`, `AsyncSessionLocal`, `select`, `func`, `and_`
- `macro.py`: `NewsItem`, `Stock`, `AsyncSessionLocal`, `select`
- `portfolio.py`: `PortfolioItem`, `Stock`, `ModelPortfolioHistory`, `AsyncSessionLocal`, `select`, `causal_engine` (lazy), `kap_parser` (lazy), `portfolio_optimizer` (lazy)
- `intelligence.py`: `event_fusion` (lazy), `correlation_engine` (lazy), `market_intelligence_service` (lazy)
- `causal.py`: `causal_engine`, `market_intelligence_service` (lazy), `knowledge_graph` (lazy)
- `admin.py`: `Stock`, `AsyncSessionLocal`, `select`, `func`, `run_kap_scan` (lazy), `scoring_engine`, `func` from `and_` — plus all top-5 queries from `get_dashboard`

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | None detected — zero test files exist in `backend/app/` |
| Config file | None — `pytest.ini`, `setup.cfg [tool:pytest]`, `pyproject.toml [pytest]` absent |
| Quick run command | `cd backend && python -m pytest tests/ -x -q` (after Wave 0 setup) |
| Full suite command | `cd backend && python -m pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FOND-01 | Startup raises RuntimeError when feedparser missing | unit | `pytest tests/test_kap_parser.py::test_startup_error_without_feedparser -x` | Wave 0 |
| FOND-01 | Empty list returned when KAP RSS unreachable | unit | `pytest tests/test_kap_parser.py::test_kap_unreachable_returns_empty -x` | Wave 0 |
| FOND-01 | `_generate_mock_announcements` no longer callable | unit | `pytest tests/test_kap_parser.py::test_no_mock_method -x` | Wave 0 |
| FOND-02 | scoring.py reads weights from settings, not BASE_WEIGHTS | unit | `pytest tests/test_scoring.py::test_weights_from_settings -x` | Wave 0 |
| FOND-02 | Changing settings.WEIGHT_TECHNICAL reflects in score calculation | unit | `pytest tests/test_scoring.py::test_weight_change_propagates -x` | Wave 0 |
| FOND-02 | Null macro_score treated as zero contribution | unit | `pytest tests/test_scoring.py::test_missing_macro_score_neutral -x` | Wave 0 |
| FOND-03 | pip install succeeds without tensorflow, torch, transformers, sentencepiece | smoke | `pip install -r requirements.txt && python -c "import tensorflow" 2>&1 \| grep "No module"` | manual |
| FOND-04 | All 31 endpoints reachable after router split | smoke | `pytest tests/test_routers.py::test_all_routes_registered -x` | Wave 0 |
| FOND-04 | endpoints.py file no longer exists | unit | `pytest tests/test_routers.py::test_endpoints_py_deleted -x` | Wave 0 |
| FOND-05 | model_portfolio generation_date column is timezone-aware | unit | `pytest tests/test_models.py::test_model_portfolio_timezone -x` | Wave 0 |
| FOND-05 | No `datetime.utcnow()` calls remain in DB write paths | static | `grep -r "datetime.utcnow()" backend/app/` (must return 0 results) | manual |

### Sampling Rate

- **Per task commit:** Quick run — `cd backend && python -m pytest tests/ -x -q`
- **Per wave merge:** Full suite — `cd backend && python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `backend/tests/__init__.py` — package init
- [ ] `backend/tests/conftest.py` — shared fixtures (mock `settings`, mock `Stock` instances)
- [ ] `backend/tests/test_kap_parser.py` — covers FOND-01 (3 tests)
- [ ] `backend/tests/test_scoring.py` — covers FOND-02 (3 tests)
- [ ] `backend/tests/test_routers.py` — covers FOND-04 (2 smoke tests)
- [ ] `backend/tests/test_models.py` — covers FOND-05 (1 test)
- [ ] Framework install: `pip install pytest pytest-asyncio` in `backend/.venv`

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `datetime.utcnow()` | `datetime.now(timezone.utc)` | Python 3.12 deprecated utcnow | utcnow() still works in 3.9 but returns naive datetime — the core bug here |
| Try/except optional imports | Hard imports with startup health checks | FastAPI lifespan pattern | Lifespan context manager is the canonical place for dependency validation |
| Class-level config constants | pydantic-settings singletons | FastAPI/pydantic v2 era | Single source of truth, overridable via .env |

**Deprecated/outdated:**
- `datetime.utcnow()`: deprecated in Python 3.12, returns tz-naive datetime. Use `datetime.now(timezone.utc)` — returns tz-aware datetime.
- `default=datetime.utcnow` (callable) as SQLAlchemy column default: Works but is Python-side (not DB-side). Prefer `server_default=func.now()` with `DateTime(timezone=True)` so the DB controls the timestamp.

---

## Open Questions

1. **vaderSentiment after transformers removal**
   - What we know: `vaderSentiment` is not pinned in requirements.txt. It is actively used in `macro_news.py`.
   - What's unclear: Whether it was being pulled as a transitive dependency of `transformers` or installed independently.
   - Recommendation: After removing the 4 ML packages, run `pip install -r requirements.txt` in a clean venv and verify `from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer` succeeds. If it fails, add `vaderSentiment` as an explicit line in requirements.txt.

2. **Crisis mode macro weight**
   - What we know: D-05 adds macro to normal-mode weights. The crisis mode override hardcodes 5 keys (no macro). After the fix, both code paths must have the same key set.
   - What's unclear: Whether macro should contribute 0.0 or be excluded from crisis mode.
   - Recommendation: Include `"macro_score": 0.0` in crisis mode weights dict (macro data lags real-time crisis signals, so 0 weight is correct). The existing score loop handles 0-weight entries gracefully.

3. **No Alembic migration vs. create_all behavior on existing DB**
   - What we know: D-14 says no Alembic migration — `create_all()` handles it on restart.
   - What's unclear: `create_all()` only ADDS columns to new tables; it does NOT alter existing tables' column types. If `model_portfolio_history` table already exists in a dev DB, changing `DateTime` to `DateTime(timezone=True)` will NOT be applied by `create_all()`.
   - Recommendation: Document in the implementation task that **developers must drop and recreate the `model_portfolio_history` table** in their local dev DB after this change, OR run: `ALTER TABLE model_portfolio_history ALTER COLUMN generation_date TYPE TIMESTAMPTZ;`. This is a dev-time concern, not production (the table is empty in prod until 18:15 daily job runs). The planner should include this step explicitly.

---

## Sources

### Primary (HIGH confidence — direct codebase inspection)

- `backend/app/services/kap_parser.py` — All 3 mock fallback locations confirmed at lines 66-68, 103, 110
- `backend/app/services/scoring.py` — `BASE_WEIGHTS` confirmed at lines 22-28; `_resolve_weights` method at lines 33-49
- `backend/app/core/config.py` — `WEIGHT_*` settings confirmed at lines 53-58; total = 1.00
- `backend/app/models/stock.py` — `macro_score` column confirmed ABSENT; `DateTime(timezone=True)` pattern confirmed present
- `backend/app/models/model_portfolio.py` — `DateTime` without timezone confirmed at lines 14-15
- `backend/app/api/endpoints.py` — All 31 endpoints enumerated and mapped
- `backend/app/main.py` — lifespan function at lines 97-139; single `include_router` at line 159
- `backend/requirements.txt` — tensorflow/torch/transformers/sentencepiece confirmed present; vaderSentiment confirmed absent (not pinned)
- `backend/app/services/macro_news.py` — vaderSentiment import confirmed at line 3

### Secondary (HIGH confidence — established Python/FastAPI conventions)

- FastAPI `APIRouter` documentation — router-per-domain is the standard pattern for large FastAPI applications
- Python datetime docs — `datetime.now(timezone.utc)` as replacement for deprecated `datetime.utcnow()`
- SQLAlchemy docs — `DateTime(timezone=True)` with `server_default=func.now()` for UTC-correct timestamps

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified in requirements.txt and codebase
- Architecture: HIGH — all 31 endpoints personally enumerated from source; patterns verified against existing working code
- Pitfalls: HIGH — all pitfalls derived from direct code inspection, not speculation

**Research date:** 2026-04-16
**Valid until:** 2026-05-16 (stable codebase, no external API dependencies in this phase)
