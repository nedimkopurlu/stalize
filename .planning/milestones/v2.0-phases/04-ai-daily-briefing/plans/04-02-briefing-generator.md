---
phase: 04-ai-daily-briefing
plan_id: "04-02"
title: "Wave 2 — briefing_generator.py core business logic"
requirement: BREF-03, BREF-04, BREF-05
wave: 2
estimated_minutes: 60
type: execute
depends_on: ["04-01"]
files_modified:
  - backend/app/services/briefing_generator.py
autonomous: true
must_haves:
  truths:
    - "generate_daily_briefing() fetches overnight KAP announcements since yesterday 18:00 Istanbul time"
    - "generate_daily_briefing() identifies notable stocks: volume > 2x 20-day avg OR abs(change) > 3%"
    - "DailyCommentary Pydantic model validates risk_summary, opportunities, watch_list"
    - "LLM failure stores partial briefing (ai_commentary=None) without crashing"
    - "Upsert is idempotent: second call with same date updates, not duplicates"
  artifacts:
    - path: "backend/app/services/briefing_generator.py"
      provides: "generate_daily_briefing(), _upsert_briefing(), _is_notable_stock(), DailyCommentary"
      min_lines: 150
  key_links:
    - from: "backend/app/services/briefing_generator.py"
      to: "backend/app/models/model_daily_briefing.py"
      via: "postgresql_insert(DailyBriefing).on_conflict_do_update(index_elements=['date'])"
    - from: "backend/app/services/briefing_generator.py"
      to: "backend/app/models/news.py"
      via: "select(NewsItem).where(source=='KAP', published_at >= start_utc)"
    - from: "backend/app/services/briefing_generator.py"
      to: "backend/app/services/llm_sentiment.py"
      via: "llm_sentiment_service._patched_client.chat.completions.create(response_model=DailyCommentary)"
---

<objective>
Build `briefing_generator.py` — the core service that collects overnight KAP data, finds notable stocks, fetches macro indicators, generates structured LLM commentary, and upserts the result to PostgreSQL.

Purpose: This is the brain of the briefing pipeline. Wave 3 only needs to schedule `generate_daily_briefing()` as a cron job.
Output: `backend/app/services/briefing_generator.py` — a self-contained async service.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/04-ai-daily-briefing/04-CONTEXT.md
@.planning/phases/04-ai-daily-briefing/RESEARCH.md
@backend/app/models/model_daily_briefing.py
@backend/app/core/database.py

<interfaces>
<!-- Existing services that briefing_generator.py calls. Extracted from codebase. -->

From backend/app/services/llm_sentiment.py (pattern confirmed in RESEARCH.md):
```python
# Module-level singleton and semaphore
llm_sentiment_service   # has ._patched_client (instructor-patched AsyncOpenAI)
                        # and .model (str — settings.LLM_MODEL)
_llm_semaphore          # asyncio.Semaphore(5) — use when calling _patched_client

# Usage pattern:
async with _llm_semaphore:
    result: DailyCommentary = await llm_sentiment_service._patched_client.chat.completions.create(
        model=llm_sentiment_service.model,
        messages=[...],
        response_model=DailyCommentary,
        temperature=0.3,
        max_tokens=800,
    )
```

From backend/app/models/news.py (NewsItem columns confirmed in RESEARCH.md):
```python
class NewsItem(Base):
    __tablename__ = "news_items"
    source = Column(String)             # "KAP" for KAP announcements
    title = Column(String)
    summary = Column(String, nullable=True)
    published_at = Column(DateTime(timezone=True))
```

From backend/app/models/stock.py (confirmed in RESEARCH.md):
```python
class Stock(Base):
    symbol = Column(String)
    is_active = Column(Boolean)
    daily_change_pct = Column(Float, nullable=True)  # Updated by data_collector daily
    volume = Column(Float, nullable=True)
    current_price = Column(Float, nullable=True)
```

From backend/app/models/price.py (confirmed in RESEARCH.md):
```python
class PriceHistory(Base):
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    date = Column(Date)
    volume = Column(Float)
    close = Column(Float)
    # Pre-computed: sma_20, sma_50, rsi_14, etc.
    # No daily_change_pct — calculate from Stock.daily_change_pct
```

From backend/app/services/tcmb_adapter.py (confirmed in RESEARCH.md):
```python
tcmb_adapter   # singleton
await tcmb_adapter.fetch_policy_rate()         # -> {"rate": float, "date": str, ...}
await tcmb_adapter.fetch_fx_reserves()         # -> {"gross_reserves_billion_usd": float, ...}
await tcmb_adapter.fetch_latest_press_release() # -> {"title": str, "summary": str, ...}
# All three fall back to mock data on network failure — safe to call concurrently
```

From backend/app/models/model_daily_briefing.py (created in Wave 1):
```python
class DailyBriefing(Base):
    __tablename__ = "daily_briefings"
    date = Column(Date, nullable=False, index=True)
    kap_summary = Column(Text, nullable=True)
    price_summary = Column(Text, nullable=True)
    macro_summary = Column(Text, nullable=True)
    notable_stocks = Column(JSON, nullable=True)
    ai_commentary = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    generation_duration_ms = Column(Integer, nullable=True)
```

PostgreSQL upsert pattern (from RESEARCH.md — BREF-02):
```python
from sqlalchemy.dialects.postgresql import insert as postgresql_insert

stmt = postgresql_insert(DailyBriefing).values(**data)
stmt = stmt.on_conflict_do_update(
    index_elements=["date"],
    set_={k: stmt.excluded[k] for k in data if k != "date"},
)
async with AsyncSessionLocal() as session:
    await session.execute(stmt)
    await session.commit()
```
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Create briefing_generator.py with DailyCommentary, data collectors, and upsert</name>
  <files>backend/app/services/briefing_generator.py</files>
  <behavior>
    - DailyCommentary(BaseModel) has: risk_summary: str, opportunities: List[str], watch_list: List[str]
    - _is_notable_stock(volume, avg_volume_20d, daily_change_pct) returns True when volume > 2*avg_volume_20d OR abs(daily_change_pct) > 3.0; False otherwise (strictly greater than, not equal)
    - overnight_window() returns (start_utc, end_utc) tuple of timezone-aware datetime objects; start is yesterday 18:00 Istanbul, end is now
    - _upsert_briefing(**kwargs) issues postgresql_insert ON CONFLICT DO UPDATE; does not update created_at on conflict
    - generate_daily_briefing() handles exceptions from each data source individually (partial briefing stored if LLM fails)
    - test_notable_stocks_algorithm, test_daily_commentary_model, test_briefing_upsert all xpass
  </behavior>
  <action>
Create `backend/app/services/briefing_generator.py` with the full implementation.

Key implementation details to follow exactly:

**1. DailyCommentary Pydantic model** — define at module top level (instructor needs it as a class, not a lambda):
```python
from pydantic import BaseModel
from typing import List

class DailyCommentary(BaseModel):
    risk_summary: str
    opportunities: List[str]
    watch_list: List[str]
```

**2. Timezone constant** — use zoneinfo (stdlib, Python 3.9+):
```python
import zoneinfo
ISTANBUL = zoneinfo.ZoneInfo("Europe/Istanbul")
```

**3. _is_notable_stock helper** — pure function, no DB:
```python
def _is_notable_stock(volume: float, avg_volume_20d: float, daily_change_pct: float) -> bool:
    """Returns True if stock passes notable threshold (BREF-04)."""
    volume_anomaly = avg_volume_20d > 0 and volume > 2 * avg_volume_20d
    price_move = abs(daily_change_pct) > 3.0  # strictly greater than 3%, not equal
    return volume_anomaly or price_move
```

**4. overnight_window()** — DST-safe via zoneinfo:
```python
import datetime as dt

def overnight_window() -> tuple:
    now_ist = dt.datetime.now(ISTANBUL)
    yesterday = now_ist.date() - dt.timedelta(days=1)
    start_ist = dt.datetime(yesterday.year, yesterday.month, yesterday.day,
                             18, 0, 0, tzinfo=ISTANBUL)
    return start_ist.astimezone(dt.timezone.utc), now_ist.astimezone(dt.timezone.utc)
```

**5. _fetch_overnight_kap(session)** — direct DB query, NOT kap_parser.fetch_latest_announcements() (per RESEARCH.md pitfall #2 — max_age_hours would filter out overnight items):
```python
from sqlalchemy import select
from app.models.news import NewsItem

async def _fetch_overnight_kap(session) -> list:
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
    result = await session.execute(stmt)
    return result.scalars().all()
```

**6. _compute_notable_stocks(session)** — find most recent PriceHistory date first (avoids holiday gap, per RESEARCH.md pitfall #5):
```python
from sqlalchemy import select, func
from app.models.price import PriceHistory
from app.models.stock import Stock

async def _compute_notable_stocks(session) -> list:
    # Find most recent available trading date
    latest_date_result = await session.execute(
        select(func.max(PriceHistory.date)).where(
            PriceHistory.date < dt.date.today()
        )
    )
    latest_date = latest_date_result.scalar_one_or_none()
    if not latest_date:
        return []

    # Cutoff: ~20 trading days ≈ 28 calendar days
    cutoff = latest_date - dt.timedelta(days=28)

    # Subquery: avg volume over last ~20 trading days per stock
    subq = (
        select(
            PriceHistory.stock_id,
            func.avg(PriceHistory.volume).label("avg_volume_20d"),
        )
        .where(PriceHistory.date >= cutoff, PriceHistory.date <= latest_date)
        .group_by(PriceHistory.stock_id)
        .subquery()
    )

    # Latest price row + stock info + avg volume
    stmt = (
        select(
            Stock.symbol,
            Stock.daily_change_pct,
            Stock.current_price,
            PriceHistory.volume,
            subq.c.avg_volume_20d,
        )
        .join(PriceHistory, PriceHistory.stock_id == Stock.id)
        .join(subq, PriceHistory.stock_id == subq.c.stock_id)
        .where(Stock.is_active == True, PriceHistory.date == latest_date)
    )
    rows = (await session.execute(stmt)).all()

    notable = []
    for row in rows:
        symbol, change_pct, price, volume, avg_vol = row
        if change_pct is None or volume is None or avg_vol is None:
            continue
        if _is_notable_stock(volume=volume, avg_volume_20d=avg_vol, daily_change_pct=change_pct):
            reasons = []
            if avg_vol > 0 and volume > 2 * avg_vol:
                reasons.append(f"Hacim anomalisi ({volume/avg_vol:.1f}x ortalama)")
            if abs(change_pct) > 3.0:
                reasons.append(f"Sert fiyat hareketi ({change_pct:+.1f}%)")
            notable.append({
                "symbol": symbol,
                "daily_change_pct": change_pct,
                "volume": volume,
                "avg_volume_20d": avg_vol,
                "reason": " | ".join(reasons),
            })

    # Sort by abs(change_pct) descending
    notable.sort(key=lambda x: abs(x["daily_change_pct"]), reverse=True)
    return notable[:20]  # cap at 20
```

**7. _fetch_macro_snapshot()** — concurrent TCMB calls, graceful on failure:
```python
import asyncio

async def _fetch_macro_snapshot() -> dict:
    from app.services.tcmb_adapter import tcmb_adapter
    policy_rate, fx_reserves, press = await asyncio.gather(
        tcmb_adapter.fetch_policy_rate(),
        tcmb_adapter.fetch_fx_reserves(),
        tcmb_adapter.fetch_latest_press_release(),
        return_exceptions=True,
    )
    return {
        "policy_rate": policy_rate if not isinstance(policy_rate, Exception) else None,
        "fx_reserves": fx_reserves if not isinstance(fx_reserves, Exception) else None,
        "press_release": press if not isinstance(press, Exception) else None,
    }
```

**8. Text summary builders** — simple prose formatters:
```python
def _summarise_kap(items: list) -> str:
    if not items:
        return "Dün saat 18:00'den bu yana yeni KAP bildirimi bulunmuyor."
    lines = [f"• {item.title} ({item.source})" for item in items[:10]]
    return f"Gece gelen {len(items)} KAP bildirimi:\n" + "\n".join(lines)

def _summarise_notable_stocks(stocks: list) -> str:
    if not stocks:
        return "Dikkat çeken hisse hareketi tespit edilmedi."
    lines = [f"• {s['symbol']}: {s['daily_change_pct']:+.1f}% — {s['reason']}" for s in stocks[:10]]
    return "Dikkat çeken hisseler:\n" + "\n".join(lines)

def _summarise_macro(macro: dict) -> str:
    parts = []
    if macro.get("policy_rate") and not isinstance(macro["policy_rate"], Exception):
        rate = macro["policy_rate"].get("rate")
        if rate:
            parts.append(f"TCMB faiz: %{rate}")
    if macro.get("fx_reserves") and not isinstance(macro["fx_reserves"], Exception):
        gross = macro["fx_reserves"].get("gross_reserves_billion_usd")
        if gross:
            parts.append(f"Brüt rezerv: ${gross:.1f}B")
    return " | ".join(parts) if parts else "Makro veri alınamadı."
```

**9. _generate_commentary()** — uses llm_sentiment_service._patched_client (Option A per RESEARCH.md):
```python
BRIEFING_SYSTEM_PROMPT = (
    "Sen BIST 100 uzmanı bir finansal analistsin. "
    "Verilen sabah brifing özetini analiz et ve günün risk ortamını, "
    "potansiyel fırsatları ve dikkat edilecek hisseleri belirt. "
    "Kısa, net ve Türkçe yaz."
)

async def _generate_commentary(kap: str, price: str, macro: str) -> DailyCommentary:
    from app.services.llm_sentiment import llm_sentiment_service, _llm_semaphore

    user_content = f"KAP Özeti:\n{kap}\n\nFiyat Hareketleri:\n{price}\n\nMakro:\n{macro}"
    async with _llm_semaphore:
        return await llm_sentiment_service._patched_client.chat.completions.create(
            model=llm_sentiment_service.model,
            messages=[
                {"role": "system", "content": BRIEFING_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            response_model=DailyCommentary,
            temperature=0.3,
            max_tokens=800,
        )
```

**10. _upsert_briefing()** — atomic PostgreSQL upsert, does NOT update created_at:
```python
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from app.core.database import AsyncSessionLocal
from app.models.model_daily_briefing import DailyBriefing

async def _upsert_briefing(**kwargs) -> None:
    stmt = postgresql_insert(DailyBriefing).values(**kwargs)
    stmt = stmt.on_conflict_do_update(
        index_elements=["date"],
        set_={k: stmt.excluded[k] for k in kwargs if k != "date"},
        # created_at intentionally excluded — preserves first-generation timestamp
    )
    async with AsyncSessionLocal() as session:
        await session.execute(stmt)
        await session.commit()
```

**11. generate_daily_briefing()** — top-level entry point for APScheduler (Wave 3):
```python
import time
import logging

logger = logging.getLogger(__name__)

async def generate_daily_briefing() -> None:
    """Entry point called by APScheduler cron (BREF-01). Orchestrates all data collection."""
    logger.info("Günlük brifing üretimi başlıyor...")
    start_ms = int(time.time() * 1000)
    today = dt.date.today()

    async with AsyncSessionLocal() as session:
        try:
            kap_items = await _fetch_overnight_kap(session)
        except Exception as e:
            logger.error(f"KAP sorgu hatası: {e}")
            kap_items = []

        try:
            notable_stocks = await _compute_notable_stocks(session)
        except Exception as e:
            logger.error(f"Notable stocks hatası: {e}")
            notable_stocks = []

    try:
        macro_data = await _fetch_macro_snapshot()
    except Exception as e:
        logger.error(f"Makro veri hatası: {e}")
        macro_data = {}

    kap_summary = _summarise_kap(kap_items)
    price_summary = _summarise_notable_stocks(notable_stocks)
    macro_summary = _summarise_macro(macro_data)

    ai_commentary = None
    try:
        commentary = await _generate_commentary(kap_summary, price_summary, macro_summary)
        ai_commentary = commentary.model_dump()
    except Exception as e:
        logger.error(f"LLM yorum hatası (kısmi brifing kaydedilecek): {e}")

    duration_ms = int(time.time() * 1000) - start_ms

    await _upsert_briefing(
        date=today,
        kap_summary=kap_summary,
        price_summary=price_summary,
        macro_summary=macro_summary,
        notable_stocks=notable_stocks,
        ai_commentary=ai_commentary,
        generation_duration_ms=duration_ms,
    )
    logger.info(f"Günlük brifing tamamlandi ({duration_ms}ms)")
```

Assemble all pieces into a single well-organized file with this section order:
1. Imports
2. Constants (ISTANBUL, BRIEFING_SYSTEM_PROMPT)
3. DailyCommentary Pydantic model
4. Pure helpers (_is_notable_stock, overnight_window)
5. Data collectors (_fetch_overnight_kap, _compute_notable_stocks, _fetch_macro_snapshot)
6. Summary builders (_summarise_kap, _summarise_notable_stocks, _summarise_macro)
7. LLM (_generate_commentary)
8. DB (_upsert_briefing)
9. Entry point (generate_daily_briefing)
  </action>
  <verify>
    <automated>cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/test_daily_briefing.py::test_notable_stocks_algorithm tests/test_daily_briefing.py::test_daily_commentary_model tests/test_daily_briefing.py::test_briefing_upsert -x -q</automated>
  </verify>
  <done>
    - `backend/app/services/briefing_generator.py` exists with all 9 sections
    - `_is_notable_stock()` is exported and pure (no DB dependency)
    - `DailyCommentary` validates correctly per BREF-05 spec
    - `_upsert_briefing()` uses postgresql_insert ON CONFLICT DO UPDATE
    - `generate_daily_briefing()` is async, handles partial failure (ai_commentary=None on LLM error)
    - test_notable_stocks_algorithm xpasses
    - test_daily_commentary_model xpasses
    - test_briefing_upsert xpasses
  </done>
</task>

</tasks>

<verification>
Run all Wave-2 stubs:
```
cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && \
  /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest \
  tests/test_daily_briefing.py::test_notable_stocks_algorithm \
  tests/test_daily_briefing.py::test_daily_commentary_model \
  tests/test_daily_briefing.py::test_briefing_upsert \
  -v
```

Expected: 3 xpass. Full suite regression check:
```
cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && \
  /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/ -q
```
</verification>

<success_criteria>
- `briefing_generator.py` exists with all described functions exported
- `DailyCommentary` Pydantic model validates correctly
- `_is_notable_stock(volume=1_000_000, avg_volume_20d=400_000, daily_change_pct=0.5)` returns True
- `_is_notable_stock(volume=100_000, avg_volume_20d=200_000, daily_change_pct=1.0)` returns False
- `_upsert_briefing` uses `postgresql_insert().on_conflict_do_update()` (not merge or raw SQL)
- LLM failure path: ai_commentary stored as None, no exception propagates
- 3 new xpass in test suite; no regressions
</success_criteria>

<rollback>
Delete `backend/app/services/briefing_generator.py`. Wave-1 files are unaffected. Tests return to xfail for Wave-2 stubs.
</rollback>

<output>
After completion, create `.planning/phases/04-ai-daily-briefing/plans/04-02-SUMMARY.md` with:
- File created: backend/app/services/briefing_generator.py
- Functions exported: generate_daily_briefing, _upsert_briefing, _is_notable_stock, DailyCommentary, overnight_window
- Tests now xpassing: test_notable_stocks_algorithm, test_daily_commentary_model, test_briefing_upsert
- Key pattern: postgresql_insert ON CONFLICT DO UPDATE on DailyBriefing.date
- Key pattern: llm_sentiment_service._patched_client reuse with _llm_semaphore
</output>
