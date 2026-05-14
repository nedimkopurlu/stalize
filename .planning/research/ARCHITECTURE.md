# Architecture Research

**Domain:** BIST stock analysis assistant — v7.0 feature integration
**Researched:** 2026-05-14
**Confidence:** HIGH (based on direct codebase inspection)

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js 16)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────┐  │
│  │ StockDetail  │  │  Portfolio   │  │ Backtest   │  │  Other   │  │
│  │  page.tsx    │  │  page.tsx    │  │  page.tsx  │  │  pages   │  │
│  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘  └────┬─────┘  │
│         └─────────────────┴────────────────┴──────────────┘        │
│                           api.ts (typed client)                      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ HTTP REST (NEXT_PUBLIC_API_URL)
┌────────────────────────────────▼────────────────────────────────────┐
│                       FastAPI /api router                            │
│  stocks.py │ portfolio_v2.py │ intelligence.py │ signals.py │ ...   │
├─────────────────────────────────────────────────────────────────────┤
│                         Services Layer                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ scoring  │ │technical │ │sentiment │ │ kap_     │ │backtest  │  │
│  │  .py     │ │  .py     │ │  .py     │ │parser.py │ │  .py     │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐   │
│  │fundamen- │ │data_     │ │model_    │ │ dynamic_correlation  │   │
│  │tal.py    │ │collector │ │portfolio │ │       .py            │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────────┘   │
├─────────────────────────────────────────────────────────────────────┤
│              APScheduler (AsyncIOScheduler — 16 jobs)                │
│  KAP 5min │ TCMB 60min │ data_update Nh │ signal_snapshot 18:20     │
│  model_portfolio 6h │ dynamic_correlation 60min │ ...               │
├─────────────────────────────────────────────────────────────────────┤
│                  PostgreSQL (asyncpg + SQLAlchemy)                   │
│  stocks │ price_history │ news_items │ portfolio_positions │ ...    │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Status for v7.0 |
|-----------|----------------|-----------------|
| `scoring.py` (ScoringEngine) | Weighted aggregation of sub-scores into final score | MODIFY — add sector branching |
| `sentiment.py` (SentimentAnalysisEngine) | Keyword-based Turkish sentiment on yfinance news | REPLACE body — delegate to turkish_nlp.py |
| `kap_parser.py` (KAPParser) | KAP RSS + API fetch, entity linking, impact scoring | MODIFY — add fine-grained classification |
| `technical.py` (TechnicalAnalysisEngine) | RSI, MACD, Bollinger, ATR, OBV, peaks | MODIFY — add weekly/monthly timeframes |
| `data_collector.py` (DataCollector) | yfinance OHLCV, fundamentals, live quotes | MODIFY — add tavan/taban detection |
| `backtest.py` (backtesting engine) | Rule-based signal simulation from stored OHLCV | MODIFY — add slippage/commission model |
| `fundamental.py` | yfinance fundamental data fetching and enrichment | MODIFY — add sanity-check quality layer |
| `dynamic_correlation.py` | Portfolio-to-portfolio and cross-sector correlation | REUSE — portfolio correlation endpoint can call this |
| `main.py` | FastAPI app, CORS, APScheduler lifecycle | MODIFY — add new scheduler jobs |
| `stocks.py` (API router) | BIST100 listing, stock detail, scoring endpoints | MODIFY — new score breakdown fields |
| `portfolio_v2.py` (API router) | Portfolio CRUD, positions, snapshots | MODIFY — add beta, correlation, sizing endpoints |
| `news.py` (model) | NewsItem ORM with category, sentiment fields | NO CHANGE — category column already exists |
| `stock.py` (model) | Stock ORM — scores, metadata | MODIFY — add liquidity_score, liquidity_label columns |
| `price.py` (model) | PriceHistory OHLCV + pre-calculated indicators | MODIFY — add is_tavan, is_taban bool columns |

## Recommended Project Structure for v7.0 Additions

```
backend/app/
├── services/
│   ├── scoring.py              # MODIFY: sector-branch logic
│   ├── sentiment.py            # MODIFY: delegate body to turkish_nlp.py
│   ├── turkish_nlp.py          # NEW: Turkish NLP service wrapper
│   ├── market_regime.py        # NEW: regime detection engine
│   ├── liquidity.py            # NEW: liquidity score computation
│   ├── portfolio_analytics.py  # NEW: beta, correlation, position sizing
│   ├── sector_scoring.py       # NEW: bank/REIT/holding adapters
│   ├── kap_parser.py           # MODIFY: classification categories
│   ├── data_collector.py       # MODIFY: tavan/taban detection
│   ├── backtest.py             # MODIFY: slippage + commission model
│   └── fundamental.py          # MODIFY: quality/sanity layer
├── models/
│   ├── stock.py                # MODIFY: liquidity_score, liquidity_label columns
│   ├── news.py                 # NO CHANGE: category column already exists
│   ├── price.py                # MODIFY: is_tavan, is_taban booleans
│   └── market_regime.py        # NEW: MarketRegime ORM model
├── api/
│   ├── stocks.py               # MODIFY: liquidity, regime in response
│   └── portfolio_v2.py         # MODIFY: beta, correlation, sizing endpoints
└── alembic/versions/
    └── XXXX_v7_schema.py       # NEW: migration for all DB changes
```

## Architectural Patterns

### Pattern 1: Sector Branching in ScoringEngine

**What:** `calculate_overall_score()` checks `stock.sector` and delegates to a sector-specific weight/metric resolver before the existing weighted sum.

**When to use:** Banks, REITs, Holdings have fundamentally different valuation metrics (NIM vs P/E, NAV discount vs P/B).

**Trade-offs:** Keeps the single ScoringEngine contract; avoids scattered scoring logic. Risk: sector string values from yfinance are inconsistent — need a normalization map.

**Implementation approach:**
```python
# scoring.py — add before weight resolution
SECTOR_WEIGHT_OVERRIDES = {
    "Bankacılık": {"fundamental_score": 0.50, "technical_score": 0.30, "sentiment_score": 0.20},
    "GYO":        {"fundamental_score": 0.45, "technical_score": 0.30, "sentiment_score": 0.25},
    "Holding":    {"fundamental_score": 0.40, "technical_score": 0.35, "sentiment_score": 0.25},
}

def _resolve_weights(self, stock: Stock) -> Dict[str, float]:
    sector = (stock.sector or "").strip()
    override = self.SECTOR_WEIGHT_OVERRIDES.get(sector)
    if override:
        return override
    # fall through to existing normalization logic
```

Extract sector-specific metric computation into `sector_scoring.py` — called only during `collect_fundamentals()`, outputs persist as sub-fields on the Fundamental row. ScoringEngine reads those fields, not yfinance directly.

### Pattern 2: Turkish NLP as a Drop-in Wrapper

**What:** Replace the keyword-based `SentimentAnalysisEngine.analyze_stock()` body with a call to a new `turkish_nlp.py` service that wraps whichever NLP backend is available.

**When to use:** BERTurk is the preferred model but is ~400MB — too large for Railway 512MB. The wrapper must degrade gracefully.

**Trade-offs:**

| Option | Size | Accuracy | Railway fit |
|--------|------|----------|-------------|
| BERTurk (HuggingFace) | ~420MB | High | NO — exceeds RAM |
| savasy/bert-base-turkish-sentiment-cased | ~420MB | High | NO |
| zemberek-python (rule + morphology) | ~5MB | Medium | YES |
| Keyword rules + morpheme awareness | <1MB | Low-medium | YES |
| Remote Gemini call (existing infra) | 0MB local | High | YES (rate-limited) |

**Recommendation:** Use Gemini 2.0 Flash for KAP announcement sentiment (already integrated, Türkçe mükemmel, 0 additional RAM) with a lightweight keyword fallback for high-frequency yfinance news items. Do NOT load BERTurk on Railway free tier.

**Implementation approach:**
```python
# turkish_nlp.py — new service
class TurkishNLPService:
    async def analyze(self, text: str, use_llm: bool = False) -> dict:
        if use_llm:
            return await self._gemini_sentiment(text)  # existing gemini_service.py
        return self._keyword_sentiment(text)           # fast path for bulk
```

`sentiment.py` imports and delegates; `kap_parser.py` uses `use_llm=True` for important announcement classification.

### Pattern 3: Market Regime as Persisted State

**What:** A new `market_regime.py` service computes BIST100-level regime (bull/bear/sideways/volatile) from index price history. Result is persisted in a new `market_regimes` table and read by ScoringEngine's `macro_regime_score` weight slot.

**When to use:** Regime computation is expensive (requires 200+ days of XU100 data). Run it on a scheduler job, not on-demand.

**Implementation approach:**
```python
# market_regime.py — new singleton
class MarketRegimeEngine:
    REGIMES = ["bull", "bear", "sideways", "volatile"]

    async def compute_regime(self) -> str:
        # reads CommodityPrice for XU100.IS (already stored)
        # applies: 200-day SMA slope + 20-day volatility percentile + drawdown
        ...

    async def get_current_regime(self) -> str:
        # reads latest row from market_regimes table
        ...
```

New DB model:
```python
# models/market_regime.py
class MarketRegime(Base):
    __tablename__ = "market_regimes"
    id = Column(Integer, primary_key=True)
    computed_at = Column(DateTime(timezone=True), server_default=func.now())
    regime = Column(String(20), nullable=False)      # bull/bear/sideways/volatile
    confidence = Column(Float, nullable=True)         # 0-1
    indicators_json = Column(JSON, nullable=True)     # raw indicators for transparency
```

Scheduler job: add `background_market_regime_update` to `main.py`, every 60 minutes, `max_instances=1`. Uses XU100.IS data from existing `CommodityPrice` table — no new data source.

### Pattern 4: Portfolio Analytics as Stateless Computation

**What:** Beta, correlation matrix, and position sizing are computed on-demand from existing DB data (PortfolioPosition + PriceHistory + CommodityPrice). No new persistence needed except optional caching.

**When to use:** These are read-heavy, compute-on-request operations. Avoid persisting to DB unless called > 5x/minute (unlikely for single-user tool).

**Trade-offs:** Avoids schema changes at the cost of ~200ms latency per call (acceptable for single user). Beta computation requires BIST100 index returns — already stored in `CommodityPrice` as `XU100.IS`.

**New endpoints in `portfolio_v2.py`:**
```
GET /api/portfolio/beta          -> {"portfolio_beta": 1.23, "period_days": 90}
GET /api/portfolio/correlation   -> {"matrix": {...}, "symbols": [...]}
GET /api/portfolio/position-size -> {"symbol": "THYAO", "suggested_pct": 5.2, "reasoning": "..."}
```

All computations in new `portfolio_analytics.py` service — stateless functions, no singleton needed.

### Pattern 5: Tavan/Taban Detection in DataCollector

**What:** After fetching daily OHLCV, compare whether `high == low` (circuit breaker) or `close >= open * 1.099` (upper limit, tavan) or `close <= open * 0.901` (taban). Flag on `PriceHistory` row.

**When to use:** Detect daily; expose via existing stock detail API response.

**DB change:** Two new boolean columns on `price_history`: `is_tavan BOOLEAN DEFAULT FALSE`, `is_taban BOOLEAN DEFAULT FALSE`. Requires Alembic migration.

**Implementation approach:** Add `_detect_circuit_breakers(df)` method to `DataCollector`; call it inside `collect_prices()` before DB upsert.

### Pattern 6: KAP Classification Without Schema Change

**What:** The `NewsItem.category` column already exists (String(50), nullable). Current values include "company_disclosure", "geopolitics", "macro", "sector". Extend the `KAPParser._classify_announcement()` method to emit more granular KAP-specific values.

**No schema change needed.** Only `kap_parser.py` changes — add a `_kap_category()` method that pattern-matches KAP title/summary against Turkish term dictionaries.

```python
KAP_CATEGORIES = {
    "temettu": ["temettü", "kar payı", "nakit kar payı"],
    "sermaye_artirimi": ["bedelsiz", "bedelli", "sermaye artırımı", "rüçhan"],
    "mali_sonuclar": ["finansal sonuçlar", "bilanço", "gelir tablosu"],
    "geri_alim": ["geri alım", "pay geri alım"],
    "yonetim_degisikligi": ["yönetim kurulu", "genel müdür", "görevden"],
}
```

The existing `category` field stores generic values. The cleanest path: write the granular KAP value directly to `category` when source is KAP. No Alembic migration required for this feature.

### Pattern 7: Backtest Slippage/Commission Model

**What:** The existing `backtest.py` `StrategySpec` and trade simulation loop apply ATR-based stops and targets. Add `slippage_bps` (basis points applied to entry/exit price) and `commission_bps` parameters to `StrategySpec` and to the trade execution calculation.

**Default values:** 20bps commission (2x10bps per side, BIST typical), 10bps slippage.

**No schema change needed.** Pure computation change in `backtest.py`. The frontend `/backtest` page receives updated KPI fields.

### Pattern 8: Multi-Timeframe Technical Analysis

**What:** Add weekly and monthly price aggregation to the technical analysis flow. Aggregate `PriceHistory` daily rows into weekly and monthly DataFrames inside `TechnicalAnalysisEngine`, compute indicators, return as separate sub-objects.

**No schema change needed** — compute from existing daily rows. New field in API response: `technical_analysis.weekly`, `technical_analysis.monthly`. Existing `daily` sub-object unchanged.

### Pattern 9: Liquidity Score

**What:** Stateless computation from existing `PriceHistory` data: average daily volume consistency (std/mean of 30-day volume), volume trend, estimated spread proxy (daily range / close). Returns a `liquidity_score` (0-100) and `thinly_traded` boolean.

**Persistence:** Store `liquidity_score` on `Stock` model (new column). Requires Alembic migration.

**Implementation:** `liquidity.py` new service with `compute_liquidity_score(price_rows: list) -> float` pure function. Called from `data_collector.daily_update()` after prices refresh.

## Data Flow

### Request Flow — New Portfolio Analytics

```
User opens Portfolio page
    ↓
portfolio/page.tsx -> api.ts -> GET /api/portfolio/beta
    ↓
portfolio_v2.py route handler
    ↓
portfolio_analytics.py.compute_beta(positions, db)
    ↓
SELECT price_history WHERE stock_id IN (positions) AND date > 90d ago
SELECT commodity_prices WHERE symbol = 'XU100.IS' AND date > 90d ago
    ↓
Compute returns, covariance, beta (numpy, in asyncio.to_thread)
    ↓
{"portfolio_beta": 1.23} -> JSON response
```

### Background Flow — Market Regime Update

```
APScheduler (every 60min) -> background_market_regime_update()
    ↓
market_regime.MarketRegimeEngine.compute_regime()
    ↓
SELECT commodity_prices WHERE symbol = 'XU100.IS' ORDER BY date DESC LIMIT 252
    ↓
Compute: 200d SMA slope, 20d volatility percentile, max drawdown 90d
    ↓
INSERT INTO market_regimes (regime, confidence, indicators_json)
    ↓
ScoringEngine reads latest regime on next update_all_scores() call
```

### Background Flow — Turkish NLP Sentiment (KAP path)

```
background_kap_scan() (every 5min)
    ↓
kap_parser.fetch_latest_announcements()
    ↓
For each announcement:
  turkish_nlp.analyze(title + summary, use_llm=True)  <- Gemini call
  _kap_category(title)  <- keyword pattern match, no LLM
    ↓
NewsItem.sentiment_score = result.score
NewsItem.category = result.kap_category
    ↓
scoring_engine.update_all_scores() if stored > 0
```

## Alembic Migration Plan

All DB changes must be consolidated into a single v7.0 Alembic revision to minimize migration risk:

| Table | Column | Type | Default | Feature |
|-------|--------|------|---------|---------|
| `stocks` | `liquidity_score` | Float | NULL | Liquidity scoring |
| `stocks` | `liquidity_label` | String(20) | NULL | "düşük"/"orta"/"yüksek" |
| `price_history` | `is_tavan` | Boolean | False | Tavan/taban detection |
| `price_history` | `is_taban` | Boolean | False | Tavan/taban detection |
| `market_regimes` | (entire new table) | — | — | Market regime engine |

`NewsItem.category` already exists — no change needed. KAP classification writes to existing column.

**Migration file:** `backend/alembic/versions/XXXX_v7_0_schema.py`

## Integration Map: New vs Modified

### Modified Components

| Component | Change Type | What Changes | Risk |
|-----------|-------------|--------------|------|
| `scoring.py` | Extend | Add `_resolve_weights(stock)` sector branch; add `market_regime_score` read | Low — additive; existing tests pass with sector=None |
| `sentiment.py` | Replace body | Delegate `analyze_stock()` to `turkish_nlp.py`; keep interface signature | Low — same return type |
| `kap_parser.py` | Extend | `_kap_category()` method + write to `category` field | Low — no schema change |
| `technical.py` | Extend | `calculate_multi_timeframe()` wrapping existing `calculate_indicators()` | Low — new method, existing unchanged |
| `data_collector.py` | Extend | `_detect_circuit_breakers()` call inside `collect_prices()`; `compute_liquidity_score()` call after price update | Medium — touches inner data loop |
| `backtest.py` | Extend | `StrategySpec` gains `slippage_bps`, `commission_bps`; trade PnL calculation updated | Low — additive fields with defaults |
| `fundamental.py` | Extend | Add `_data_quality_check()` wrapper around yfinance fetch; returns quality score | Low — wraps existing logic |
| `portfolio_v2.py` | Extend | Three new GET routes: `/beta`, `/correlation`, `/position-size` | Low — new routes, no existing routes change |
| `stocks.py` | Extend | Include `liquidity_score`, `is_tavan`, `is_taban` in stock detail response | Low — additive response fields |
| `main.py` | Extend | Add `background_market_regime_update` scheduler job | Low — follows existing pattern |
| `models/stock.py` | Additive | `liquidity_score`, `liquidity_label` columns | Low — nullable, Alembic migration |
| `models/price.py` | Additive | `is_tavan`, `is_taban` boolean columns | Low — default False, Alembic migration |

### New Components

| Component | Purpose | Dependencies |
|-----------|---------|--------------|
| `services/turkish_nlp.py` | Turkish NLP wrapper (Gemini + keyword fallback) | `gemini_service.py` (existing) |
| `services/market_regime.py` | MarketRegimeEngine singleton; regime computation | `CommodityPrice` table (XU100.IS data) |
| `services/liquidity.py` | Liquidity score computation | `PriceHistory` table |
| `services/portfolio_analytics.py` | Beta, correlation matrix, position sizing — stateless | `PriceHistory`, `CommodityPrice`, `PortfolioPosition` |
| `services/sector_scoring.py` | Bank NIM/NPL, REIT NAV, Holding NAV adapters | `fundamental.py`, yfinance |
| `models/market_regime.py` | MarketRegime ORM table | `Base` from database |
| `alembic/versions/XXXX_v7_0_schema.py` | Single migration for all v7 schema changes | — |

## Scaling Considerations

| Concern | Current (1 user) | Notes |
|---------|-----------------|-------|
| Portfolio analytics latency | 200-500ms per call | Acceptable; add in-memory cache if needed later |
| Turkish NLP (Gemini) KAP calls | ~5 calls/5min cycle | Gemini quota fallback already implemented |
| Market regime computation | 1x60min job, <5MB | Light; only reads existing CommodityPrice |
| Multi-timeframe technical | 3x computation per stock | On-demand only, not in bulk scheduler |
| Liquidity score bulk | 100 stocks in daily_update | Sequential, not parallel — yfinance rate-limit safe |

**Railway 512MB RAM constraint — per feature:**

| Feature | RAM impact | Assessment |
|---------|-----------|------------|
| Turkish NLP (Gemini path) | 0MB additional | SAFE — remote call |
| Turkish NLP (BERTurk) | +420MB | BLOCKED — exceeds limit |
| Market Regime Engine | <5MB | SAFE — pure pandas/numpy |
| Portfolio Analytics | <10MB | SAFE — small DataFrames |
| Liquidity Score | <5MB | SAFE — existing data |
| Multi-timeframe Technical | <20MB | SAFE — existing `ta` lib |
| Sector Scoring (yfinance only) | <10MB | SAFE |

## Build Order — Suggested Phase Sequence

Dependencies drive this ordering. Each phase is independently deployable:

**Phase 1 — Foundation (unblocks everything else)**
- Alembic migration: `is_tavan`, `is_taban`, `liquidity_score`, `market_regimes` table
- `safeLabel()` moved to `StockHelpers.tsx` (tech debt — unblocks UI consistency)
- yfinance data quality layer in `fundamental.py`

**Phase 2 — Data Enrichment (populates new columns, no new endpoints)**
- Tavan/taban detection in `data_collector.py`
- Liquidity score in `liquidity.py` + wired into `data_collector.py`
- KAP announcement classification in `kap_parser.py`

**Phase 3 — Regime + Turkish NLP (new services, feeds scoring)**
- `market_regime.py` + scheduler job + `market_regimes` table reads
- `turkish_nlp.py` + wire into `sentiment.py` and `kap_parser.py`

**Phase 4 — Scoring Depth (depends on Phase 2+3 data being in DB)**
- `sector_scoring.py` adapters (bank NIM/NPL, REIT NAV, holding NAV)
- `scoring.py` sector branching + regime integration
- Multi-timeframe technical analysis in `technical.py`

**Phase 5 — Portfolio Analytics (depends on Phase 1 schema only)**
- `portfolio_analytics.py` — beta, correlation, position sizing
- New API routes in `portfolio_v2.py`
- Pre-trade checklist frontend component (reads regime + scoring + liquidity)

**Phase 6 — Backtest Quality + UI Polish (independent of all above)**
- Slippage/commission model in `backtest.py`
- Stock detail page hierarchy restructure
- Post-trade learning loop UI

Note: Phase 5 can run in parallel with Phases 3-4 since it only needs Phase 1 schema.

## Anti-Patterns

### Anti-Pattern 1: Loading BERTurk on Railway Free Tier

**What people do:** Install `transformers` + BERTurk model — it is the "best" Turkish NLP option.

**Why it is wrong:** Model weights alone are ~420MB; combined with existing TensorFlow (~600MB) and PyTorch (~800MB) already in requirements.txt, total memory blows through Railway's 512MB worker limit on first request.

**Do this instead:** Route KAP sentiment through existing Gemini 2.0 Flash integration (`gemini_service.py`). Use keyword/morpheme rules for bulk yfinance news. BERTurk is a valid future option only if TensorFlow and PyTorch are removed or the project moves to a paid tier.

### Anti-Pattern 2: Computing Portfolio Beta Inside the API Request Handler

**What people do:** Place numpy covariance computation directly in the FastAPI route function.

**Why it is wrong:** Blocks the async event loop for ~200ms during DB reads + computation. Fine for one user, breaks under concurrent requests.

**Do this instead:** `portfolio_analytics.py` uses `asyncio.to_thread()` for the numpy computation, keeping DB queries async and CPU work off the event loop.

### Anti-Pattern 3: New Scheduler Jobs Without max_instances=1

**What people do:** Add new APScheduler jobs without `max_instances=1` guard.

**Why it is wrong:** Overlapping job executions cause DB lock contention and double-processing on startup catch-up. All 16 existing jobs in `main.py` already set `max_instances=1`.

**Do this instead:** Every new scheduler job must have `max_instances=1` and a `misfire_grace_time` appropriate to its interval.

### Anti-Pattern 4: Multiple Alembic Migrations for v7.0 Schema Changes

**What people do:** Create one migration per feature as features are built.

**Why it is wrong:** On Railway, each deploy runs `alembic upgrade head`. Multiple small migrations create a fragile chain — one failure blocks all subsequent ones.

**Do this instead:** Batch all v7.0 schema additions (tavan/taban, liquidity_score, market_regimes table) into a single `XXXX_v7_0_schema.py` migration, created in Phase 1.

### Anti-Pattern 5: Raw yfinance Sector String Comparison

**What people do:** `stock.sector == "Bankacılık"` comparison directly in ScoringEngine.

**Why it is wrong:** yfinance returns inconsistent sector strings for BIST stocks (English/Turkish mix, sometimes None). Direct string comparison fails silently for most stocks.

**Do this instead:** Create a `SECTOR_NORMALIZE` map in `config.py` that normalizes raw yfinance sector strings to canonical values. ScoringEngine uses only canonical values.

### Anti-Pattern 6: Parallel yfinance Calls for Bulk Liquidity/Quality Computation

**What people do:** Use `asyncio.gather()` across all 100 BIST stocks to compute liquidity in parallel.

**Why it is wrong:** yfinance rate-limits batch requests. Existing `data_collector.py` uses sequential fetching with intentional delays for this reason.

**Do this instead:** Compute liquidity score from already-fetched `PriceHistory` rows (already in DB) — no new yfinance call needed. Rate-limit risk eliminated.

## Integration Points

### External Services

| Service | Integration Pattern | Notes for v7.0 |
|---------|---------------------|----------------|
| Gemini 2.0 Flash | Existing `gemini_service.py` | Reuse for KAP sentiment; 15 req/min means max ~12 KAP items per 5-min scan window |
| yfinance | Existing `data_collector.py` + `fundamental.py` | Data quality layer wraps existing calls; no new yfinance endpoints needed |
| XU100.IS index data | Already stored in `CommodityPrice` by data_collector | Market regime reads from this table — zero new external calls |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `scoring.py` to `market_regime.py` | Direct import; `get_current_regime()` async DB read | ScoringEngine must await regime read |
| `scoring.py` to `sector_scoring.py` | Direct import; sector metrics pre-computed, stored in Fundamental row | ScoringEngine reads from DB, not live yfinance |
| `sentiment.py` to `turkish_nlp.py` | Direct import; same async interface | Keyword path is synchronous; Gemini path is async |
| `kap_parser.py` to `turkish_nlp.py` | Direct import; `use_llm=True` for important items | Rate-limit guard inside `turkish_nlp.py` |
| `portfolio_v2.py` to `portfolio_analytics.py` | Direct import; stateless functions | `asyncio.to_thread()` for CPU-heavy correlation matrix |
| `data_collector.py` to `liquidity.py` | Direct import; `compute_liquidity_score()` pure function | Called after `collect_prices()` in daily update loop |

## Sources

- Direct codebase inspection: `backend/app/main.py`, `services/scoring.py`, `services/sentiment.py`, `services/kap_parser.py`, `services/backtest.py`, `services/technical.py`, `services/data_collector.py`, `models/stock.py`, `models/news.py`, `models/price.py`, `models/portfolio_v2.py`
- PROJECT.md v7.0 requirements (`.planning/PROJECT.md`)
- Railway free tier constraints: 512MB RAM, 1 vCPU (from milestone context)
- Gemini 2.0 Flash limits: 15 req/min, 1500 req/day (from PROJECT.md Key Decisions)

---
*Architecture research for: Yatırım Asistanı v7.0 — Analiz Kalitesi & Sistem Bütünlüğü*
*Researched: 2026-05-14*
