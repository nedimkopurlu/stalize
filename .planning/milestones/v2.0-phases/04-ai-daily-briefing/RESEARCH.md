# Phase 4: AI Daily Briefing — Research

**Researched:** 2026-04-17
**Domain:** APScheduler cron + PostgreSQL ORM upsert + instructor DailyCommentary + BIST price mover detection
**Confidence:** HIGH (all findings drawn from direct codebase inspection)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- BREF-01: APScheduler cron job, weekdays only (`day_of_week="mon-fri"`), 06:30 **Europe/Istanbul** local time. Same `scheduler` instance already in `main.py`.
- BREF-02: `DailyBriefing` SQLAlchemy ORM model — one row per calendar date (unique constraint on `date`). `GET /api/briefing/today` must respond in <100 ms (reads from DB, no LLM at request time). Upsert-safe: `INSERT ... ON CONFLICT DO UPDATE`.
- BREF-03: Briefing content — (1) overnight KAP announcements since yesterday 18:00, (2) top price movers from previous close, (3) macro snapshot (USD/TRY, TCMB rate, inflation). LLM synthesises into prose.
- BREF-04: Notable stocks — `volume > 2× 20-day avg` OR `abs(change) > 3%`. List with symbol, reason, score.
- BREF-05: Net AI commentary — `DailyCommentary` Pydantic model (`risk_summary`, `opportunities`, `watch_list`) via instructor. Failure stores partial briefing (ai_commentary = None).
- DailyBriefing columns: `id`, `date` (Date, unique), `kap_summary` (Text), `price_summary` (Text), `macro_summary` (Text), `notable_stocks` (JSON), `ai_commentary` (JSON), `created_at` (DateTime(timezone=True)), `generation_duration_ms` (Integer).
- File locations: `backend/app/models/model_daily_briefing.py`, `backend/app/services/briefing_generator.py`, `backend/app/api/briefing.py` (add endpoint).
- 404 body when no record: `{"detail": "Brifing henüz üretilmedi"}`.
- `X-Cache: HIT` response header on every successful DB read.

### Claude's Discretion
All implementation choices within the constraints above.

### Deferred Ideas (OUT OF SCOPE)
- Push notification when briefing is ready (v2)
- Manual regeneration endpoint (v2)
- Multi-day briefing history (v2)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BREF-01 | APScheduler cron weekdays 06:30 Europe/Istanbul | Cron pattern confirmed in §APScheduler Patterns below |
| BREF-02 | DailyBriefing ORM model (unique on date, upsert-safe); GET /api/briefing/today <100ms | ORM schema + PostgreSQL upsert pattern documented below |
| BREF-03 | Content = overnight KAP + top price movers + macro snapshot → LLM prose | kap_parser query pattern + PriceHistory columns + TCMB adapter documented |
| BREF-04 | Notable stocks = volume > 2× 20-day avg OR abs(change) > 3% | PriceHistory.volume, Stock.daily_change_pct columns confirmed; SQL pattern documented |
| BREF-05 | Net AI commentary = DailyCommentary(risk_summary, opportunities, watch_list) via instructor | instructor client pattern from llm_sentiment.py fully documented |
</phase_requirements>

---

## Summary

Phase 4 adds a pre-generated morning briefing pipeline on top of the existing APScheduler + PostgreSQL + instructor infrastructure. All four service layers that feed the briefing (KAP, price history, TCMB macro, LLM) already exist as singletons; the implementation work is purely about wiring them into a new `briefing_generator.py` service, a new `DailyBriefing` ORM model, and a new endpoint on the already-registered `briefing.py` router.

The two most technically nuanced requirements are the PostgreSQL upsert (INSERT ... ON CONFLICT DO UPDATE via SQLAlchemy 2.0 `insert(...).on_conflict_do_update()`) and the overnight KAP window query (NewsItem WHERE source='KAP' AND published_at >= yesterday 18:00 Istanbul → UTC). The existing codebase handles timezone-aware datetimes consistently with `DateTime(timezone=True)` throughout, so the overnight window calculation needs the `pytz` or `zoneinfo` conversion to UTC before querying.

The briefing `GET /api/briefing/today` endpoint is a simple primary-key lookup by today's `date` column — with the `UNIQUE INDEX` on `date`, this is a single-row fetch guaranteed to be well under 100 ms.

**Primary recommendation:** Build `briefing_generator.py` as a self-contained async function `generate_daily_briefing()` that (1) queries existing tables, (2) builds prose with instructor, (3) upserts to `daily_briefings` using `postgresql_insert`. Register it in `main.py` lifespan with a cron job mirroring the TUIK pattern already present.

---

## Existing Code Analysis

### 1. `backend/app/api/briefing.py` — DOES NOT EXIST YET

The file `backend/app/api/briefing.py` was referenced in CONTEXT.md as "Phase 1 created this router." However, direct filesystem inspection confirmed the file **does not exist**. The `main.py` router imports are:
```python
from app.api import stocks, macro, portfolio, intelligence, causal, admin
```
There is no `briefing` import. This means Phase 4 must both **create** `briefing.py` from scratch AND register it in `main.py`.

**Action required:** Create `backend/app/api/briefing.py` with APIRouter and register `app.include_router(briefing.router, prefix="/api")` in `main.py`.

### 2. `backend/app/main.py` — APScheduler Setup

The scheduler is an `AsyncIOScheduler` module-level singleton:
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
scheduler = AsyncIOScheduler()
```

Jobs are registered inside the `lifespan` async context manager (before `scheduler.start()`). Two existing patterns are directly reusable:

**Interval pattern (existing):**
```python
scheduler.add_job(background_macro_scan, "interval", hours=1)
scheduler.add_job(background_kap_scan, "interval", minutes=settings.KAP_SCAN_INTERVAL_MIN)
```

**Cron pattern (existing, closest to BREF-01):**
```python
# TUIK: weekdays at 09:00 — no timezone arg (uses scheduler default)
scheduler.add_job(background_tuik_scan, "cron", day_of_week="mon-fri", hour=9, minute=0)

# Audit: weekdays at 18:05
scheduler.add_job(background_audit_and_learn, "cron", day_of_week="mon-fri", hour=18, minute=5)
```

**CRITICAL FINDING:** Existing cron jobs do NOT pass a `timezone` argument. The scheduler itself is instantiated as `AsyncIOScheduler()` with no timezone argument, which defaults to the local system timezone. For BREF-01 (06:30 Europe/Istanbul), the job MUST specify `timezone="Europe/Istanbul"` explicitly, otherwise correctness depends on the server OS timezone.

**Correct BREF-01 cron registration:**
```python
scheduler.add_job(
    generate_daily_briefing,
    "cron",
    day_of_week="mon-fri",
    hour=6,
    minute=30,
    timezone="Europe/Istanbul",
)
```

APScheduler 3.11.0 (confirmed in requirements.txt) accepts `timezone` as a string (`"Europe/Istanbul"`) directly — it resolves via `pytz` or `zoneinfo` internally.

---

## Standard Stack

### Core (all already in requirements.txt)
| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| apscheduler | 3.11.0 | Cron job for 06:30 | `AsyncIOScheduler`, `"cron"` trigger |
| sqlalchemy[asyncio] | 2.0.40 | ORM model + upsert | `postgresql_insert` dialect upsert |
| asyncpg | 0.30.0 | Async PostgreSQL driver | Already configured |
| instructor | 1.15.1 | Structured LLM output | `Mode.JSON` for DeepSeek |
| pydantic | 2.11.1 | `DailyCommentary` model | Same version as StockAnalysis |

### No new dependencies required.
All packages needed for Phase 4 are already installed.

---

## Architecture Patterns

### ORM Model Conventions (from inspection)

All existing models follow the same pattern. The closest analogue to `DailyBriefing` is `ModelPortfolioHistory` (one row per business-day, unique constraint on a date column, JSON column stored as `String`):

```python
# backend/app/models/model_portfolio.py — reference pattern
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base

class ModelPortfolioHistory(Base):
    __tablename__ = "model_portfolio_history"
    id = Column(Integer, primary_key=True, index=True)
    generation_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    allocations_json = Column(String, default="[]")   # JSON stored as String
    __table_args__ = (UniqueConstraint('target_date', name='uq_target_date'),)
```

**DailyBriefing must follow this pattern exactly.** Key decisions derived from codebase inspection:

1. JSON columns (`notable_stocks`, `ai_commentary`) → use `sqlalchemy.dialects.postgresql.JSON` or `String`. Existing code uses `String` for JSON. Use `JSON` type from `sqlalchemy` for the briefing to enable richer PostgreSQL-side querying — but both work for the <100ms endpoint.
2. Unique constraint on `date` (not `DateTime`) — use `UniqueConstraint('date', name='uq_briefing_date')`.
3. No `Relationship` needed — `DailyBriefing` is a standalone table.
4. File naming: existing pattern uses both `model_name.py` (e.g., `model_portfolio.py`) and plain `name.py` (e.g., `price.py`, `news.py`). CONTEXT.md specifies `model_daily_briefing.py` — follow that.

**`DailyBriefing` schema:**
```python
# backend/app/models/model_daily_briefing.py
from sqlalchemy import Column, Integer, Date, Text, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql import func
from app.core.database import Base

class DailyBriefing(Base):
    __tablename__ = "daily_briefings"
    __table_args__ = (
        UniqueConstraint("date", name="uq_briefing_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    kap_summary = Column(Text, nullable=True)
    price_summary = Column(Text, nullable=True)
    macro_summary = Column(Text, nullable=True)
    notable_stocks = Column(JSON, nullable=True)       # List[dict]
    ai_commentary = Column(JSON, nullable=True)        # DailyCommentary dict or None
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    generation_duration_ms = Column(Integer, nullable=True)
```

### models/__init__.py must be updated
Add to import list:
```python
from app.models.model_daily_briefing import DailyBriefing
```
And add `"DailyBriefing"` to `__all__`. This is how `Base.metadata.create_all` at startup will discover and create the `daily_briefings` table automatically (no Alembic migration needed — Alembic directory is empty/unused; project relies on `create_all`).

---

## PostgreSQL Upsert Pattern (BREF-02)

**Context:** SQLAlchemy 2.0 async does not support the ORM-level `merge()` pattern for upsert. The correct approach is the `postgresql`-dialect `insert(...).on_conflict_do_update()`. This is what CONTEXT.md specifies.

**Pattern:**
```python
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from app.models.model_daily_briefing import DailyBriefing
from app.core.database import AsyncSessionLocal
import datetime

async def upsert_daily_briefing(data: dict) -> None:
    stmt = postgresql_insert(DailyBriefing).values(**data)
    stmt = stmt.on_conflict_do_update(
        index_elements=["date"],   # unique constraint column
        set_={
            "kap_summary": stmt.excluded.kap_summary,
            "price_summary": stmt.excluded.price_summary,
            "macro_summary": stmt.excluded.macro_summary,
            "notable_stocks": stmt.excluded.notable_stocks,
            "ai_commentary": stmt.excluded.ai_commentary,
            "generation_duration_ms": stmt.excluded.generation_duration_ms,
            # created_at intentionally NOT updated — preserves first-generation timestamp
        },
    )
    async with AsyncSessionLocal() as session:
        await session.execute(stmt)
        await session.commit()
```

**Important:** `index_elements` must reference the column(s) covered by a `UNIQUE` constraint or index (not just `__table_args__` UniqueConstraint name). Both work in PostgreSQL but `index_elements=["date"]` is the explicit form.

**Why not `session.merge()`?** SQLAlchemy async ORM `merge()` performs a SELECT then INSERT or UPDATE, which is two round trips and not idempotent under concurrent callers. `on_conflict_do_update` is a single atomic statement.

---

## KAP Overnight Window Query (BREF-03)

**What `kap_parser` provides:**
- `KAPParser.fetch_latest_announcements()` — fetches live RSS, returns raw dicts. Not suitable for overnight query (fetches only from live feed, subject to `max_age_hours` config).
- `KAPParser.get_recent_feed(limit=20)` — queries `NewsItem` table (WHERE source='KAP'), ordered by `published_at DESC`, limited to 20.
- `KAPParser.get_recent_scenarios(limit=10)` — similar, returns scenario dicts.

**None of these have a date-range filter.** The overnight window (yesterday 18:00 Istanbul → now) requires a direct database query.

**Correct overnight window query:**
```python
from datetime import datetime, date, timedelta
import zoneinfo

ISTANBUL = zoneinfo.ZoneInfo("Europe/Istanbul")

def overnight_window() -> tuple[datetime, datetime]:
    """Returns (start_utc, end_utc) for overnight KAP window."""
    now_ist = datetime.now(ISTANBUL)
    today_ist = now_ist.date()
    yesterday_ist = today_ist - timedelta(days=1)
    # Start: yesterday 18:00 Istanbul
    start_ist = datetime(yesterday_ist.year, yesterday_ist.month, yesterday_ist.day,
                         18, 0, 0, tzinfo=ISTANBUL)
    # End: now
    return start_ist.astimezone(datetime.timezone.utc), now_ist.astimezone(datetime.timezone.utc)
```

**SQL query:**
```python
from sqlalchemy import select
from app.models.news import NewsItem

start_utc, end_utc = overnight_window()
stmt = (
    select(NewsItem)
    .where(
        NewsItem.source == "KAP",
        NewsItem.published_at >= start_utc,
        NewsItem.published_at <= end_utc,
    )
    .order_by(NewsItem.published_at.desc())
    .limit(30)
)
```

**Note on `zoneinfo`:** Python 3.9+ ships `zoneinfo` in stdlib. The project uses Python 3.9 (confirmed via `.venv/lib/python3.9`). `zoneinfo.ZoneInfo("Europe/Istanbul")` works without `pytz`. However, `pytz` is likely available as a transitive dep of APScheduler — either works.

---

## Price Mover Detection (BREF-03, BREF-04)

**PriceHistory columns confirmed:**
- `stock_id`, `date` (Date), `open`, `high`, `low`, `close`, `volume` (Float)
- `adj_close` (Float, nullable)
- Pre-calculated: `sma_20`, `sma_50`, `sma_200`, `rsi_14`, `macd`, `bb_upper/middle/lower`, `atr_14`, `obv`
- **No `daily_change_pct` column on PriceHistory** — this must be calculated.

**Stock table columns confirmed:**
- `current_price`, `daily_change_pct` (Float, nullable), `volume` (Float, nullable)

**Two approaches for price movers:**

*Approach A — Use `Stock.daily_change_pct` (fast, single-table):*
```python
# Top movers from Stock table (cached by data_collector)
from sqlalchemy import select, func
from app.models.stock import Stock

stmt = (
    select(Stock)
    .where(Stock.is_active == True, Stock.daily_change_pct != None)
    .order_by(func.abs(Stock.daily_change_pct).desc())
    .limit(10)
)
```
Risk: `Stock.daily_change_pct` is updated by `data_collector._collect_stock_prices()` which runs during daily updates; at 06:30 the value reflects yesterday's close. Acceptable for a morning briefing.

*Approach B — Compute from last two PriceHistory rows (accurate):*
Requires a self-join or subquery — more expensive. Not needed given Approach A is sufficient.

**BREF-04 Notable stocks volume anomaly — 20-day average volume query:**
```python
from sqlalchemy import select, func
from app.models.price import PriceHistory
from app.models.stock import Stock
import datetime

# Subquery: avg volume over last 20 trading days per stock
cutoff = datetime.date.today() - datetime.timedelta(days=28)  # ~20 trading days

subq = (
    select(
        PriceHistory.stock_id,
        func.avg(PriceHistory.volume).label("avg_volume_20d"),
    )
    .where(PriceHistory.date >= cutoff)
    .group_by(PriceHistory.stock_id)
    .subquery()
)

# Latest PriceHistory row per stock (yesterday's close)
yesterday = datetime.date.today() - datetime.timedelta(days=1)
latest = (
    select(PriceHistory, Stock.symbol, Stock.daily_change_pct, subq.c.avg_volume_20d)
    .join(Stock, PriceHistory.stock_id == Stock.id)
    .join(subq, PriceHistory.stock_id == subq.c.stock_id)
    .where(PriceHistory.date == yesterday)
    .where(
        (PriceHistory.volume > (2 * subq.c.avg_volume_20d))
        | (func.abs(Stock.daily_change_pct) > 3.0)
    )
    .order_by(func.abs(Stock.daily_change_pct).desc())
)
```

**Note:** `yesterday` should be the most recent trading day in the DB, not necessarily `today - 1`. Consider using `select(func.max(PriceHistory.date))` first to get the latest date.

---

## instructor DailyCommentary Client (BREF-05)

**Existing pattern from `llm_sentiment.py` (confirmed):**
```python
from openai import AsyncOpenAI
import instructor

client = AsyncOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1"
)
patched = instructor.from_openai(client, mode=instructor.Mode.JSON)
# Mode.JSON is REQUIRED for DeepSeek — Mode.JSON_SCHEMA causes 400 error

result: MyModel = await patched.chat.completions.create(
    model=settings.LLM_MODEL,
    messages=[...],
    response_model=MyModel,
    temperature=0.2,
    max_tokens=500,
)
```

**For `DailyCommentary`, two options:**

*Option A — Reuse `DeepSeekSentimentService._patched_client` directly:*
`llm_sentiment_service._patched_client` is a module-level singleton with an already-patched instructor client. `briefing_generator.py` can call it directly:
```python
from app.services.llm_sentiment import llm_sentiment_service

result: DailyCommentary = await llm_sentiment_service._patched_client.chat.completions.create(
    model=llm_sentiment_service.model,
    messages=[{"role": "system", "content": BRIEFING_SYSTEM_PROMPT},
              {"role": "user", "content": briefing_input}],
    response_model=DailyCommentary,
    temperature=0.3,
    max_tokens=800,
)
```
This reuses the existing semaphore-guarded singleton. **Recommended.**

*Option B — Create a new instructor client in `briefing_generator.py`:*
Clean separation but wastes a second connection pool. Only worth it if briefing LLM calls need different concurrency settings.

**`DailyCommentary` Pydantic model:**
```python
from pydantic import BaseModel
from typing import List

class DailyCommentary(BaseModel):
    risk_summary: str          # 1-2 sentences: main risk for today
    opportunities: List[str]   # 2-3 specific tickers or themes
    watch_list: List[str]      # symbols to watch with brief reason
```

**Semaphore:** The existing `_llm_semaphore = asyncio.Semaphore(5)` in `llm_sentiment.py` is module-level and shared. If `briefing_generator` uses `_patched_client` directly (Option A), it bypasses the semaphore. The briefing job runs once at 06:30 — no concurrent callers expected. Wrapping with the semaphore is optional but safe:
```python
from app.services.llm_sentiment import llm_sentiment_service, _llm_semaphore

async with _llm_semaphore:
    result = await llm_sentiment_service._patched_client.chat.completions.create(...)
```

---

## TCMB Macro Snapshot (BREF-03)

`tcmb_adapter.py` provides three fetch methods:
- `fetch_policy_rate()` → `{"rate": float, "date": str, "change_bps": int, "status": str}`
- `fetch_fx_reserves()` → `{"gross_reserves_billion_usd": float, "net_reserves_billion_usd": float, ...}`
- `fetch_latest_press_release()` → `{"title": str, "summary": str, "url": str, "interest_rate_decision": bool, ...}`

**All three fall back to mock data on network failure** (confirmed — each method calls `_generate_mock_*`). The briefing macro snapshot can safely call all three concurrently:
```python
policy_rate, fx_reserves, press = await asyncio.gather(
    tcmb_adapter.fetch_policy_rate(),
    tcmb_adapter.fetch_fx_reserves(),
    tcmb_adapter.fetch_latest_press_release(),
    return_exceptions=True,
)
```
USD/TRY is NOT directly available from `tcmb_adapter` — it returns FX reserves (a balance-sheet figure), not the spot rate. USD/TRY spot is available via `CommodityPrice` table (symbol `"USDTRY=X"` or similar from `settings.CURRENCY_PAIRS`) or via `get_ticker_history("USDTRY=X", period="2d")`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PostgreSQL upsert | Manual SELECT + INSERT/UPDATE two-step | `postgresql_insert(...).on_conflict_do_update()` | Atomic, race-condition safe |
| Timezone conversion | Manual UTC offset arithmetic | `zoneinfo.ZoneInfo("Europe/Istanbul")` | DST-safe |
| LLM structured output | JSON string parsing + manual validation | `instructor` with `response_model=` | Already installed; handles retries, validation |
| Cron scheduling | `asyncio.sleep` loop | `APScheduler AsyncIOScheduler` cron trigger | Already running in process |
| Price fetching | Direct yfinance call in briefing_generator | `get_ticker_history()` from `data_collector` | Has 5-min diskcache; avoids duplicate Yahoo requests |

---

## Common Pitfalls

### Pitfall 1: Missing `timezone=` on APScheduler cron job
**What goes wrong:** `scheduler.add_job(..., "cron", hour=6, minute=30)` fires at 06:30 in the server's OS timezone, not Istanbul time. In production (UTC server), this would fire at 06:30 UTC = 09:30 Istanbul.
**Root cause:** Existing jobs in `main.py` don't pass `timezone` because they either run at fixed intervals or the server is assumed to run in Istanbul timezone. The pattern is not documented in the codebase.
**How to avoid:** Always pass `timezone="Europe/Istanbul"` for this job.

### Pitfall 2: `briefing.py` router not imported in `main.py`
**What goes wrong:** Router exists but 404 on all `/api/briefing/*` endpoints.
**Root cause:** `main.py` currently imports `stocks, macro, portfolio, intelligence, causal, admin` only. `briefing` is missing.
**How to avoid:** Add `from app.api import ..., briefing` and `app.include_router(briefing.router, prefix="/api")`.

### Pitfall 3: `on_conflict_do_update` requires an actual unique index, not just constraint
**What goes wrong:** `index_elements=["date"]` fails if PostgreSQL's planner can't find a unique index on `date`. The `UniqueConstraint` in `__table_args__` creates a unique index automatically on `create_all`, so this is safe — but only after the table is first created (first app start).
**How to avoid:** The model's `UniqueConstraint("date", name="uq_briefing_date")` in `__table_args__` is sufficient. `create_all` in `lifespan` will create both the table and the index. No manual migration needed.

### Pitfall 4: Overnight window uses naive datetime vs. timezone-aware
**What goes wrong:** `NewsItem.published_at` is `DateTime(timezone=True)` — stored as UTC in PostgreSQL. If the overnight window bounds are naive datetimes, the `>=` comparison may silently fail or raise a database error with asyncpg.
**Root cause:** `asyncpg` with `asyncio` and `DateTime(timezone=True)` columns requires tz-aware datetime objects in WHERE clauses.
**How to avoid:** Always use `datetime.now(zoneinfo.ZoneInfo("Europe/Istanbul"))` and `.astimezone(timezone.utc)` before passing to SQLAlchemy queries.

### Pitfall 5: `notable_stocks` latest PriceHistory date may not be "yesterday"
**What goes wrong:** If markets were closed yesterday (weekend, holiday), `PriceHistory.date == today - 1` returns no rows.
**Root cause:** KAP scan runs Mon-Fri but holidays are not tracked.
**How to avoid:** Query the most-recent available date: `SELECT MAX(date) FROM price_history WHERE date < today`. Use that as the reference date.

### Pitfall 6: `ai_commentary = None` on LLM failure — JSON column constraint
**What goes wrong:** If the PostgreSQL column is `JSON NOT NULL`, storing `None` raises an integrity error.
**Root cause:** `nullable=True` must be set on the JSON column.
**How to avoid:** `ai_commentary = Column(JSON, nullable=True)` — confirmed in the schema above.

### Pitfall 7: `briefing_generator` DB session vs. `get_db` dependency
**What goes wrong:** APScheduler background jobs run outside of FastAPI's request lifecycle — `get_db()` FastAPI dependency injection is not available.
**Root cause:** `get_db()` is a FastAPI Depends generator, not usable outside request handlers.
**How to avoid:** Use `async with AsyncSessionLocal() as session:` directly (same pattern as `background_xgb_retrain` in `main.py`).

---

## Code Examples

### APScheduler cron registration (BREF-01)
```python
# In main.py lifespan, after other scheduler.add_job calls:
scheduler.add_job(
    generate_daily_briefing,
    "cron",
    day_of_week="mon-fri",
    hour=6,
    minute=30,
    timezone="Europe/Istanbul",
)
```

### GET /api/briefing/today endpoint (BREF-02)
```python
# backend/app/api/briefing.py
import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.model_daily_briefing import DailyBriefing

router = APIRouter(prefix="/briefing", tags=["briefing"])

@router.get("/today")
async def get_today_briefing(db: AsyncSession = Depends(get_db)):
    today = datetime.date.today()
    result = await db.execute(
        select(DailyBriefing).where(DailyBriefing.date == today)
    )
    briefing = result.scalar_one_or_none()
    if briefing is None:
        raise HTTPException(status_code=404, detail="Brifing henüz üretilmedi")

    # Convert to dict for JSON response
    data = {
        "date": briefing.date.isoformat(),
        "kap_summary": briefing.kap_summary,
        "price_summary": briefing.price_summary,
        "macro_summary": briefing.macro_summary,
        "notable_stocks": briefing.notable_stocks,
        "ai_commentary": briefing.ai_commentary,
        "created_at": briefing.created_at.isoformat() if briefing.created_at else None,
        "generation_duration_ms": briefing.generation_duration_ms,
    }
    return JSONResponse(content=data, headers={"X-Cache": "HIT"})
```

### briefing_generator skeleton (BREF-03, BREF-04, BREF-05)
```python
# backend/app/services/briefing_generator.py
import asyncio
import logging
import datetime
import time
import zoneinfo
from typing import Optional
from pydantic import BaseModel
from typing import List
from sqlalchemy.dialects.postgresql import insert as postgresql_insert

from app.core.database import AsyncSessionLocal
from app.models.model_daily_briefing import DailyBriefing
from app.services.kap_parser import kap_parser
from app.services.tcmb_adapter import tcmb_adapter
from app.services.llm_sentiment import llm_sentiment_service, _llm_semaphore

logger = logging.getLogger(__name__)

ISTANBUL = zoneinfo.ZoneInfo("Europe/Istanbul")

class DailyCommentary(BaseModel):
    risk_summary: str
    opportunities: List[str]
    watch_list: List[str]


async def generate_daily_briefing() -> None:
    """Entry point called by APScheduler cron job (BREF-01)."""
    logger.info("Günlük brifing üretimi başlıyor...")
    start_ms = int(time.time() * 1000)

    today = datetime.date.today()

    # 1. Gather data concurrently
    kap_items, macro_data, notable_stocks = await asyncio.gather(
        _fetch_overnight_kap(),
        _fetch_macro_snapshot(),
        _compute_notable_stocks(),
        return_exceptions=True,
    )

    # Handle gather exceptions gracefully
    if isinstance(kap_items, Exception):
        logger.error(f"KAP fetch failed: {kap_items}")
        kap_items = []
    if isinstance(macro_data, Exception):
        logger.error(f"Macro fetch failed: {macro_data}")
        macro_data = {}
    if isinstance(notable_stocks, Exception):
        logger.error(f"Notable stocks failed: {notable_stocks}")
        notable_stocks = []

    # 2. Build text summaries
    kap_summary = _summarise_kap(kap_items)
    price_summary = _summarise_price_movers(notable_stocks)
    macro_summary = _summarise_macro(macro_data)

    # 3. LLM commentary (BREF-05) — partial briefing if LLM fails
    ai_commentary: Optional[dict] = None
    try:
        commentary = await _generate_commentary(kap_summary, price_summary, macro_summary)
        ai_commentary = commentary.model_dump()
    except Exception as e:
        logger.error(f"LLM commentary failed (partial briefing will be stored): {e}")

    duration_ms = int(time.time() * 1000) - start_ms

    # 4. Upsert to DB
    await _upsert_briefing(
        date=today,
        kap_summary=kap_summary,
        price_summary=price_summary,
        macro_summary=macro_summary,
        notable_stocks=notable_stocks,
        ai_commentary=ai_commentary,
        generation_duration_ms=duration_ms,
    )
    logger.info(f"Günlük brifing tamamlandı ({duration_ms}ms)")


async def _upsert_briefing(**kwargs) -> None:
    stmt = postgresql_insert(DailyBriefing).values(**kwargs)
    stmt = stmt.on_conflict_do_update(
        index_elements=["date"],
        set_={k: stmt.excluded[k] for k in kwargs if k != "date"},
    )
    async with AsyncSessionLocal() as session:
        await session.execute(stmt)
        await session.commit()
```

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.x with asyncio_mode=auto |
| Config file | `backend/pytest.ini` — exists, `asyncio_mode = auto` |
| Quick run command | `cd backend && python -m pytest tests/test_briefing.py -x -q` |
| Full suite command | `cd backend && python -m pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BREF-01 | APScheduler cron registered with correct timezone | unit | `pytest tests/test_briefing.py::test_scheduler_job_registered -x` | Wave 0 |
| BREF-02 | DailyBriefing ORM columns present; upsert idempotent | unit | `pytest tests/test_briefing.py::test_daily_briefing_model -x` | Wave 0 |
| BREF-02 | GET /api/briefing/today returns 404 when no record | integration | `pytest tests/test_briefing.py::test_get_today_briefing_404 -x` | Wave 0 |
| BREF-02 | GET /api/briefing/today returns data + X-Cache header | integration | `pytest tests/test_briefing.py::test_get_today_briefing_hit -x` | Wave 0 |
| BREF-03 | overnight_window() returns correct UTC bounds | unit | `pytest tests/test_briefing.py::test_overnight_window -x` | Wave 0 |
| BREF-04 | Notable stocks filter: volume > 2× avg OR change > 3% | unit | `pytest tests/test_briefing.py::test_notable_stocks_filter -x` | Wave 0 |
| BREF-05 | DailyCommentary Pydantic model validates fields | unit | `pytest tests/test_briefing.py::test_daily_commentary_model -x` | Wave 0 |
| BREF-05 | Partial briefing stored when LLM fails | unit | `pytest tests/test_briefing.py::test_briefing_llm_failure_partial -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd backend && python -m pytest tests/test_briefing.py -x -q`
- **Per wave merge:** `cd backend && python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_briefing.py` — covers all BREF-01 through BREF-05 above
- [ ] No new conftest changes needed — existing `conftest.py` with MagicMock fixtures is sufficient; DB-touching tests should use mock/patch approach consistent with existing test files

---

## State of the Art

| Old Approach | Current Approach | Notes |
|--------------|------------------|-------|
| `session.merge()` for upsert | `postgresql_insert().on_conflict_do_update()` | SQLAlchemy 2.0 preferred pattern |
| `pytz` for timezone | `zoneinfo` (stdlib, Python 3.9+) | No extra dep needed |
| APScheduler `BackgroundScheduler` | `AsyncIOScheduler` | Required for async jobs |

---

## Open Questions

1. **USD/TRY spot rate source for macro snapshot**
   - What we know: `tcmb_adapter` provides FX reserves (not spot rate). `CommodityPrice` table stores currency data from yfinance (symbol likely `"USDTRY=X"` per `settings.CURRENCY_PAIRS`).
   - What's unclear: The exact symbol key in `settings.CURRENCY_PAIRS` is not visible without reading `config.py`.
   - Recommendation: Query `SELECT close FROM commodity_prices WHERE symbol LIKE '%USDTRY%' ORDER BY date DESC LIMIT 1`. Fallback: `get_ticker_history("USDTRY=X", period="2d")`.

2. **`settings.KAP_MAX_AGE_HOURS` may filter out overnight KAP items before they reach the DB**
   - What we know: `KAPParser.fetch_latest_announcements()` skips items older than `max_age_hours`. If this is set to e.g. 4 hours, announcements from 18:00 yesterday (12+ hours old at 06:30) may not be in the DB.
   - What's unclear: The value of `settings.KAP_MAX_AGE_HOURS` without reading `config.py`.
   - Recommendation: The briefing generator should query the `news_items` table directly (already populated by the 5-minute KAP scan job), not call `fetch_latest_announcements()` again. This bypasses `max_age_hours` entirely.

3. **`briefing.py` router file does not exist — needs creation, not modification**
   - CONTEXT.md said "Phase 1 created this router." This is incorrect. Phase 4 must create it from scratch and add it to `main.py` imports.

---

## Sources

### Primary (HIGH confidence — direct file inspection)
- `backend/app/main.py` — APScheduler singleton, cron job patterns, lifespan pattern
- `backend/app/services/llm_sentiment.py` — instructor client creation, `Mode.JSON`, semaphore
- `backend/app/core/database.py` — `AsyncSessionLocal`, `Base`, `get_db`
- `backend/app/models/price.py` — `PriceHistory` columns confirmed
- `backend/app/models/stock.py` — `Stock.daily_change_pct`, `Stock.volume` confirmed
- `backend/app/models/model_portfolio.py` — JSON-as-String, UniqueConstraint pattern
- `backend/app/models/__init__.py` — import pattern for new model
- `backend/app/services/kap_parser.py` — `get_recent_feed`, `NewsItem` query pattern
- `backend/app/services/data_collector.py` — `get_ticker_history` with diskcache
- `backend/app/services/tcmb_adapter.py` — available methods, mock fallbacks
- `backend/requirements.txt` — confirmed package versions
- `backend/pytest.ini` — `asyncio_mode = auto`
- `backend/tests/conftest.py` — existing fixture pattern

### Secondary (MEDIUM confidence)
- SQLAlchemy 2.0 docs pattern for `postgresql_insert().on_conflict_do_update()` — consistent with codebase's SQLAlchemy 2.0.40 usage
- APScheduler 3.x `timezone` string parameter — standard documented feature

---

## Metadata

**Confidence breakdown:**
- APScheduler cron pattern: HIGH — code read directly from main.py
- DailyBriefing ORM schema: HIGH — derived from existing model conventions
- PostgreSQL upsert: HIGH — standard SQLAlchemy 2.0 pattern, matches installed version
- KAP overnight query: HIGH — NewsItem schema confirmed; timezone pattern standard Python 3.9
- instructor DailyCommentary: HIGH — exact client code read from llm_sentiment.py
- Notable stocks algorithm: HIGH — PriceHistory.volume confirmed; SQL pattern standard
- TCMB macro methods: HIGH — all three methods read and documented
- USD/TRY source: MEDIUM — depends on config.py not read; workaround documented

**Research date:** 2026-04-17
**Valid until:** 2026-05-17 (stable stack)
