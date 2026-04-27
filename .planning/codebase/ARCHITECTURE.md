# Architecture

**Analysis Date:** 2026-04-16

## Pattern Overview

**Overall:** Full-Stack Monorepo — Decoupled Backend API + Frontend SPA

**Key Characteristics:**
- Python FastAPI backend with async PostgreSQL, accessed exclusively via REST
- Next.js 15 frontend (App Router, all pages are `'use client'` React hooks)
- Autonomous background scheduler (APScheduler) drives all data ingestion pipelines
- Domain logic is split into specialized singleton service engines; no shared service layer on the frontend

## Layers

**Configuration Layer:**
- Purpose: Centralized settings loaded from environment; single source of truth for all constants including BIST100 symbols, API keys, weights, and source catalog
- Location: `backend/app/core/config.py`
- Contains: `Settings` (pydantic-settings `BaseSettings` subclass), singleton `settings` object
- Depends on: `.env` file, environment variables
- Used by: every backend service and API layer

**Database Layer:**
- Purpose: Async SQLAlchemy engine, session factory, and declarative base
- Location: `backend/app/core/database.py`
- Contains: `async_engine`, `sync_engine` (for Alembic), `AsyncSessionLocal`, `Base`, `get_db()` dependency, `init_db()`
- Depends on: `settings.DATABASE_URL`
- Used by: all service singletons and endpoint handlers (direct `AsyncSessionLocal()` context managers, not injected `get_db()` in most services)

**Models Layer:**
- Purpose: SQLAlchemy ORM table definitions; data shape is authoritative here
- Location: `backend/app/models/`
- Contains: `Stock`, `PriceHistory`, `CommodityPrice`, `Fundamental`, `NewsItem`, `Recommendation`, `PortfolioItem`, `GeopoliticalEvent`, `MacroIndicator`, `CausalChainLog`, `ModelPortfolioHistory`
- Depends on: `Base` from database layer
- Used by: service layer, API endpoints

**Service Layer:**
- Purpose: All business logic — data collection, technical/fundamental/ML/causal/sentiment analysis, scoring, portfolio optimization
- Location: `backend/app/services/`
- Contains: 20 specialized modules, each exposes a singleton engine (e.g., `scoring_engine`, `technical_engine`, `causal_engine`)
- Depends on: models, core config, external APIs (yfinance, KAP RSS, TCMB, TUIK, DeepSeek LLM)
- Used by: API endpoints, APScheduler background tasks

**API Layer:**
- Purpose: Single FastAPI router exposing all REST endpoints consumed by the frontend
- Location: `backend/app/api/endpoints.py`
- Contains: One `APIRouter` with all routes (portfolio, model-portfolio, stocks, rankings, causal, scoring, sectors, health, macro, intelligence, correlation)
- Depends on: service singletons, models, `AsyncSessionLocal`
- Used by: `main.py` which mounts it at `/api`

**Scheduler Layer:**
- Purpose: Autonomous background tasks that run data ingestion and AI processes on schedule
- Location: `backend/app/main.py` (lifespan context manager)
- Contains: `AsyncIOScheduler` with 8 jobs — macro scan (1h), KAP scan (5 min), TCMB scan (2h), TUIK scan (weekdays 9:00), event fusion (1h), dynamic correlation (Monday 9:30), AI audit (weekdays 18:05), model portfolio generation (weekdays 18:15)
- Depends on: service singletons
- Used by: invoked automatically on startup

**Frontend API Client:**
- Purpose: Single typed wrapper around all backend REST calls; type contracts defined here
- Location: `frontend/src/lib/api.ts`
- Contains: `apiFetch<T>()` generic, all interface types (`StockSummary`, `DashboardData`, `CausalScenarioResult`, `PortfolioResponse`, etc.), exported `api` object with named methods
- Depends on: `NEXT_PUBLIC_API_URL` env var (default: `http://localhost:8000/api`)
- Used by: all frontend page components

**Frontend UI Layer:**
- Purpose: Next.js App Router pages and reusable components; all pages are client components
- Location: `frontend/src/app/` (pages), `frontend/src/components/` (shared UI)
- Contains: pages for Dashboard, Intelligence, Faz9 (Macro), Stocks, Stock Detail, Causal, Model Portfolio, Sectors, Rankings, Portfolio
- Depends on: `api` client in `frontend/src/lib/api.ts`
- Used by: end users via browser

## Data Flow

**Scheduled Data Ingestion:**

1. APScheduler triggers a background function (e.g., `background_kap_scan`)
2. Service (e.g., `KAPParser`) fetches from external source (KAP RSS, yfinance, TCMB, TUIK)
3. Service writes raw data into PostgreSQL models (`NewsItem`, `PriceHistory`, `MacroIndicator`)
4. On new data stored, `scoring_engine.update_all_scores()` is called
5. `ScoringEngine` reads all active `Stock` records, recalculates weighted `overall_score` and `recommendation`, writes back

**User Request Flow:**

1. Browser page component calls `api.<method>()` from `frontend/src/lib/api.ts`
2. `apiFetch<T>()` sends HTTP request to `http://localhost:8000/api/<endpoint>`
3. FastAPI router in `backend/app/api/endpoints.py` handles the request
4. Endpoint opens `AsyncSessionLocal()`, queries models, may call service singleton methods
5. Returns JSON; `apiFetch` types response as `T`; component updates React state

**Causal Analysis Flow:**

1. `KnowledgeGraph` singleton (`backend/app/services/knowledge_graph.py`) is built at startup — nodes are economic variables (monetary, inflation, geopolitical, commodity, currency), edges are causal relationships with strength/direction/delay/confidence
2. `CausalEngine.analyze_scenario()` traverses the graph from a trigger node, propagates impact scores through chains
3. Each chain result is mapped to affected BIST100 sectors and individual stocks
4. Results are stored in `CausalChainLog` and surfaced via `/api/causal/*` endpoints

**Score Computation:**

1. Five sub-scores are stored directly on the `Stock` row: `technical_score`, `fundamental_score`, `sentiment_score`, `causal_score`, `ml_score`
2. `ScoringEngine._resolve_weights()` uses base weights (Technical 30%, Fundamental 20%, ML 15%, Causal 20%, Sentiment 15%) but shifts to crisis weights when sentiment or causal deviates >20-25 points from neutral (50)
3. `overall_score` (0-100) and `recommendation` (GÜÇLÜ AL / AL / TUT / SAT / GÜÇLÜ SAT) are written back to `Stock`

## Key Abstractions

**ScoringEngine (`backend/app/services/scoring.py`):**
- Purpose: Weighted aggregation of sub-scores into a single actionable recommendation
- Pattern: Singleton (`scoring_engine`); methods are `calculate_overall_score(stock)` and `update_all_scores()`

**CausalEngine + KnowledgeGraph (`backend/app/services/causal.py`, `backend/app/services/knowledge_graph.py`):**
- Purpose: Graph traversal that answers "if X changes → which stocks are affected and how?"
- Pattern: `KnowledgeGraph` builds an in-memory directed graph at startup; `CausalEngine` holds a reference to it and performs BFS-style propagation

**DataCollector (`backend/app/services/data_collector.py`):**
- Purpose: Orchestrates all external data pulls (yfinance prices, fundamentals, commodities, currencies, indices)
- Pattern: Singleton; called from scripts and scheduler tasks

**Frontend `api` object (`frontend/src/lib/api.ts`):**
- Purpose: Single point of truth for all typed API contracts between frontend and backend
- Pattern: Plain object of named async functions; all types defined as exported interfaces in the same file

## Entry Points

**Backend:**
- Location: `backend/app/main.py`
- Triggers: `uvicorn app.main:app` (see `start.sh`)
- Responsibilities: Creates FastAPI app, attaches CORS middleware, mounts `router` at `/api`, runs lifespan (DB init, scheduler start)

**Frontend:**
- Location: `frontend/src/app/layout.tsx` (root layout), `frontend/src/app/page.tsx` (Dashboard)
- Triggers: `npm run dev` via Next.js (see `start.sh`)
- Responsibilities: `layout.tsx` sets HTML lang and global metadata; each page component is self-contained with its own data loading

**Scripts (one-off / maintenance):**
- `backend/scripts/initial_load.py` — seed BIST100 stocks into database
- `backend/scripts/update_ai.py` — manual AI score refresh
- `backend/scripts/update_fundamentals.py` — manual fundamentals refresh
- `backend/scripts/backtester.py` — historical backtesting

## Error Handling

**Strategy:** Fail-soft with logging; services catch exceptions internally and log errors without crashing the scheduler loop

**Patterns:**
- All background scheduler functions wrap service calls in `try/except Exception as e: logging.error(...)`
- Frontend `apiFetch<T>` throws on non-OK HTTP; page components catch in a top-level `try/catch` and set an `error` state for display
- Services that depend on optional packages (XGBoost, feedparser) guard with `try/except ImportError` at module level and degrade gracefully

## Cross-Cutting Concerns

**Logging:** Python stdlib `logging`; each module creates `logger = logging.getLogger(__name__)`; SQLAlchemy engine set to `WARNING` in production
**Validation:** Pydantic `BaseModel` for request bodies (e.g., `PortfolioCreate`); pydantic-settings for config; no runtime validation on service layer internals
**Authentication:** None — CORS is open (`allow_origins=["*"]`); no auth middleware present

---

*Architecture analysis: 2026-04-16*
