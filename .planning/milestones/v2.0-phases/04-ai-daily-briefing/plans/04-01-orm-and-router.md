---
phase: 04-ai-daily-briefing
plan_id: "04-01"
title: "Wave 1 — DailyBriefing ORM model + briefing router"
requirement: BREF-02
wave: 1
estimated_minutes: 30
type: execute
depends_on: ["04-00"]
files_modified:
  - backend/app/models/model_daily_briefing.py
  - backend/app/models/__init__.py
  - backend/app/api/briefing.py
  - backend/app/main.py
autonomous: true
must_haves:
  truths:
    - "DailyBriefing table is created by create_all on startup"
    - "GET /api/briefing/today returns 404 with Turkish detail when no record exists today"
    - "GET /api/briefing/today returns 200 with X-Cache: HIT when a record exists"
    - "Endpoint responds from DB lookup with no LLM calls at request time"
  artifacts:
    - path: "backend/app/models/model_daily_briefing.py"
      provides: "DailyBriefing SQLAlchemy ORM model"
      contains: "UniqueConstraint.*uq_briefing_date"
    - path: "backend/app/api/briefing.py"
      provides: "GET /briefing/today endpoint"
      exports: ["router"]
    - path: "backend/app/models/__init__.py"
      provides: "DailyBriefing in Base.metadata for create_all"
    - path: "backend/app/main.py"
      provides: "briefing router registered at /api prefix"
  key_links:
    - from: "backend/app/main.py"
      to: "backend/app/api/briefing.py"
      via: "include_router(briefing.router, prefix='/api')"
    - from: "backend/app/api/briefing.py"
      to: "backend/app/models/model_daily_briefing.py"
      via: "select(DailyBriefing).where(DailyBriefing.date == today)"
    - from: "backend/app/models/__init__.py"
      to: "backend/app/models/model_daily_briefing.py"
      via: "from app.models.model_daily_briefing import DailyBriefing"
---

<objective>
Create the `DailyBriefing` ORM model, register it so `create_all` picks it up, create the `briefing.py` router with `GET /briefing/today`, and wire the router into `main.py`. No business logic — the generator (Wave 2) and scheduler (Wave 3) come later.

Purpose: Establishes the data contract (table schema + API shape) that all subsequent waves build against.
Output: `model_daily_briefing.py`, `api/briefing.py`, updates to `models/__init__.py` and `main.py`.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/04-ai-daily-briefing/04-CONTEXT.md
@.planning/phases/04-ai-daily-briefing/RESEARCH.md
@backend/app/models/__init__.py
@backend/app/models/model_portfolio.py
@backend/app/core/database.py
@backend/app/main.py

<interfaces>
<!-- Key patterns the executor needs. Extracted from codebase. -->

From backend/app/core/database.py:
```python
AsyncSessionLocal  # async_sessionmaker, used directly in background jobs
Base               # DeclarativeBase — all models inherit from this
async def get_db() -> AsyncSession  # FastAPI Depends dependency
```

From backend/app/models/model_portfolio.py (reference pattern for ORM model):
```python
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

From backend/app/main.py (router wiring pattern):
```python
from app.api import stocks, macro, portfolio, intelligence, causal, admin
app.include_router(stocks.router, prefix="/api")
```
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Create DailyBriefing ORM model and register in models/__init__.py</name>
  <files>backend/app/models/model_daily_briefing.py, backend/app/models/__init__.py</files>
  <behavior>
    - model has columns: id (Integer PK), date (Date, not nullable, indexed), kap_summary (Text nullable), price_summary (Text nullable), macro_summary (Text nullable), notable_stocks (JSON nullable), ai_commentary (JSON nullable), created_at (DateTime timezone=True, server_default func.now()), generation_duration_ms (Integer nullable)
    - UniqueConstraint on "date" named "uq_briefing_date" in __table_args__
    - __tablename__ = "daily_briefings"
    - models/__init__.py imports DailyBriefing and adds "DailyBriefing" to __all__
    - test_daily_briefing_model_fields xpasses after this task
  </behavior>
  <action>
Create `backend/app/models/model_daily_briefing.py`:

```python
"""
DailyBriefing ORM model — Phase 4: AI Daily Briefing (BREF-02).

One row per calendar date. Unique constraint on `date` enables
idempotent upsert via ON CONFLICT DO UPDATE.
"""
from sqlalchemy import Column, Integer, Date, Text, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql import func

from app.core.database import Base


class DailyBriefing(Base):
    """Pre-generated morning briefing record. One row per calendar date."""

    __tablename__ = "daily_briefings"

    __table_args__ = (
        UniqueConstraint("date", name="uq_briefing_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)

    # Textual summaries for each section
    kap_summary = Column(Text, nullable=True)       # Overnight KAP announcements prose
    price_summary = Column(Text, nullable=True)     # Top price movers prose
    macro_summary = Column(Text, nullable=True)     # Macro snapshot prose

    # JSON sections
    notable_stocks = Column(JSON, nullable=True)    # List[dict] — symbol, reason, score
    ai_commentary = Column(JSON, nullable=True)     # DailyCommentary dict or None on LLM failure

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    generation_duration_ms = Column(Integer, nullable=True)
```

Then update `backend/app/models/__init__.py` — add after the last existing import:

```python
from app.models.model_daily_briefing import DailyBriefing
```

And add `"DailyBriefing"` to the `__all__` list.

This makes `DailyBriefing` discoverable by `Base.metadata.create_all` in the lifespan startup.
  </action>
  <verify>
    <automated>cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/test_daily_briefing.py::test_daily_briefing_model_fields -x -q</automated>
  </verify>
  <done>
    - `model_daily_briefing.py` exists with all 9 columns plus UniqueConstraint
    - `models/__init__.py` imports DailyBriefing and lists it in __all__
    - `test_daily_briefing_model_fields` passes (xpass)
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Create briefing API router and register in main.py</name>
  <files>backend/app/api/briefing.py, backend/app/main.py</files>
  <behavior>
    - GET /api/briefing/today returns 404 JSON {"detail": "Brifing henüz üretilmedi"} when no row for today
    - GET /api/briefing/today returns 200 JSONResponse with X-Cache: HIT header when row exists
    - Response body includes: date, kap_summary, price_summary, macro_summary, notable_stocks, ai_commentary, created_at (ISO string), generation_duration_ms
    - main.py imports briefing from app.api and registers briefing.router with prefix="/api"
    - test_briefing_today_endpoint_404 and test_briefing_today_endpoint_200 xpass
  </behavior>
  <action>
Create `backend/app/api/briefing.py` from scratch (file does NOT exist — do not assume Phase 1 created it):

```python
"""
Briefing API Router — Phase 4: AI Daily Briefing (BREF-02).

GET /api/briefing/today
  - Reads from daily_briefings table (no LLM at request time)
  - Returns 404 if no record exists for today
  - Returns 200 with X-Cache: HIT header if record exists
  - Target latency: <100ms (single-row DB lookup by indexed date column)
"""
import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.model_daily_briefing import DailyBriefing

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/briefing", tags=["briefing"])


@router.get("/today")
async def get_today_briefing(db: AsyncSession = Depends(get_db)):
    """
    Return today's pre-generated morning briefing.

    Returns 404 with Turkish error message if the cron job has not yet run.
    Returns 200 + X-Cache: HIT header if the briefing exists.
    """
    today = datetime.date.today()
    result = await db.execute(
        select(DailyBriefing).where(DailyBriefing.date == today)
    )
    briefing = result.scalar_one_or_none()

    if briefing is None:
        raise HTTPException(status_code=404, detail="Brifing henüz üretilmedi")

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

Then update `backend/app/main.py`:

1. Change the import line from:
   `from app.api import stocks, macro, portfolio, intelligence, causal, admin`
   to:
   `from app.api import stocks, macro, portfolio, intelligence, causal, admin, briefing`

2. Add after the last `app.include_router(...)` call (before the root endpoint):
   `app.include_router(briefing.router, prefix="/api")`

Do NOT modify any other part of main.py.
  </action>
  <verify>
    <automated>cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/test_daily_briefing.py::test_briefing_today_endpoint_404 tests/test_daily_briefing.py::test_briefing_today_endpoint_200 -x -q</automated>
  </verify>
  <done>
    - `backend/app/api/briefing.py` exists with GET /briefing/today endpoint
    - `main.py` imports `briefing` and calls `app.include_router(briefing.router, prefix="/api")`
    - Both 404 and 200 endpoint tests xpass
    - `python -m pytest tests/ -x -q` shows no regression in existing tests
  </done>
</task>

</tasks>

<verification>
Run both test stubs from Wave 0 that cover BREF-02:

```
cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && \
  /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest \
  tests/test_daily_briefing.py::test_daily_briefing_model_fields \
  tests/test_daily_briefing.py::test_briefing_today_endpoint_404 \
  tests/test_daily_briefing.py::test_briefing_today_endpoint_200 \
  -v
```

Expected: 3 xpass. Plus existing test suite green:
```
cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && \
  /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/ -q --ignore=tests/test_daily_briefing.py
```
</verification>

<success_criteria>
- `DailyBriefing` model has all 9 required columns with correct types and nullable settings
- `UniqueConstraint("date", name="uq_briefing_date")` in `__table_args__`
- `models/__init__.py` imports and exports `DailyBriefing`
- `api/briefing.py` router exists, GET /briefing/today implemented
- 404 returns `{"detail": "Brifing henüz üretilmedi"}`
- 200 returns `X-Cache: HIT` header and all briefing fields
- `main.py` registers `briefing.router` with prefix `/api`
- 3 Wave-0 stubs now xpass (model fields, 404, 200)
- No regression in pre-existing test suite
</success_criteria>

<rollback>
Remove `backend/app/models/model_daily_briefing.py` and `backend/app/api/briefing.py`. Revert `models/__init__.py` (remove DailyBriefing import + __all__ entry). Revert `main.py` (remove briefing import and include_router call). Tests return to xfail.
</rollback>

<output>
After completion, create `.planning/phases/04-ai-daily-briefing/plans/04-01-SUMMARY.md` with:
- Files created: model_daily_briefing.py, api/briefing.py
- Files modified: models/__init__.py, main.py
- Tests now xpassing: test_daily_briefing_model_fields, test_briefing_today_endpoint_404, test_briefing_today_endpoint_200
- Table schema: daily_briefings (9 columns, unique on date)
- Endpoint: GET /api/briefing/today
</output>
