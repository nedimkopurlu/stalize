# Codebase Structure

**Analysis Date:** 2026-04-16

## Directory Layout

```
stalize/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── main.py             # FastAPI app, lifespan, APScheduler setup
│   │   ├── api/
│   │   │   └── endpoints.py    # All REST routes (single file, ~38k chars)
│   │   ├── core/
│   │   │   ├── config.py       # pydantic-settings: all app constants
│   │   │   └── database.py     # SQLAlchemy engine, session factory, Base
│   │   ├── models/
│   │   │   ├── __init__.py     # Re-exports all ORM models
│   │   │   ├── stock.py        # Stock table with all score columns
│   │   │   ├── price.py        # PriceHistory, CommodityPrice
│   │   │   ├── fundamental.py  # Fundamental ratios per stock
│   │   │   ├── news.py         # NewsItem (KAP + macro news)
│   │   │   ├── recommendation.py
│   │   │   ├── portfolio.py    # PortfolioItem (user holdings)
│   │   │   ├── geopolitics.py  # GeopoliticalEvent, MacroIndicator, CausalChainLog
│   │   │   └── model_portfolio.py  # ModelPortfolioHistory (AI-generated)
│   │   └── services/
│   │       ├── data_collector.py     # yfinance orchestrator
│   │       ├── technical.py          # TA indicators + scoring (ta library)
│   │       ├── fundamental.py        # PE/PB/dividend ratios
│   │       ├── sentiment.py          # Basic sentiment scoring
│   │       ├── llm_sentiment.py      # DeepSeek LLM sentiment
│   │       ├── ml.py                 # XGBoost price prediction
│   │       ├── scoring.py            # Weighted score aggregation engine
│   │       ├── causal.py             # Causal chain traversal engine
│   │       ├── knowledge_graph.py    # In-memory economic causal graph
│   │       ├── kap_parser.py         # KAP RSS feed parser
│   │       ├── tcmb_adapter.py       # TCMB macro data adapter
│   │       ├── tuik_adapter.py       # TUIK economic data adapter
│   │       ├── macro_news.py         # General macro news collection
│   │       ├── event_fusion.py       # Cross-source event deduplication
│   │       ├── dynamic_correlation.py # Rolling correlation matrix
│   │       ├── market_intelligence.py # Combined intelligence layer
│   │       ├── portfolio_optimizer.py # AI model portfolio generation
│   │       ├── performance_monitor.py # AI audit + feedback loop
│   │       └── translator.py         # Financial term translation
│   ├── scripts/
│   │   ├── initial_load.py     # One-time DB seed for BIST100 stocks
│   │   ├── update_ai.py        # Manual AI score refresh
│   │   ├── update_fundamentals.py
│   │   └── backtester.py       # Historical backtest runner
│   ├── alembic/                # DB migration files (empty, auto-create used instead)
│   ├── knowledge/              # Static knowledge files (JSON/YAML for graph)
│   ├── requirements.txt
│   └── .env                    # Local secrets (not committed)
├── frontend/                   # Next.js 15 (App Router, TypeScript)
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx           # Root layout (HTML shell, global metadata)
│   │   │   ├── globals.css          # Global design tokens and utility classes
│   │   │   ├── page.tsx             # / Dashboard
│   │   │   ├── page.module.css
│   │   │   ├── intelligence/
│   │   │   │   ├── page.tsx         # /intelligence Market intelligence feed
│   │   │   │   └── intelligence.module.css
│   │   │   ├── faz9/
│   │   │   │   └── page.tsx         # /faz9 TCMB/TUIK/Fusion/Correlation dashboard
│   │   │   ├── stocks/
│   │   │   │   ├── page.tsx         # /stocks Stock list with filters
│   │   │   │   └── [symbol]/
│   │   │   │       ├── page.tsx     # /stocks/[symbol] Stock detail
│   │   │   │       └── stock.module.css
│   │   │   ├── causal/
│   │   │   │   └── page.tsx         # /causal Causal scenario explorer
│   │   │   ├── model-portfolio/
│   │   │   │   └── page.tsx         # /model-portfolio AI portfolio
│   │   │   ├── sectors/
│   │   │   │   └── page.tsx         # /sectors Sector summary
│   │   │   ├── rankings/
│   │   │   │   └── page.tsx         # /rankings Score rankings
│   │   │   └── portfolio/
│   │   │       ├── page.tsx         # /portfolio User portfolio + alerts
│   │   │       └── portfolio.module.css
│   │   ├── components/
│   │   │   ├── Sidebar.tsx          # Navigation sidebar (all routes)
│   │   │   ├── Sidebar.module.css
│   │   │   ├── ScoreRing.tsx        # SVG ring score visualizer
│   │   │   └── StockHelpers.tsx     # RecommendationBadge, PriceChange, formatters
│   │   └── lib/
│   │       └── api.ts               # Typed API client + all interface definitions
│   ├── public/                      # Static assets
│   ├── next.config.ts               # Next.js config (Turbopack enabled)
│   ├── tsconfig.json
│   ├── eslint.config.mjs
│   └── package.json
├── .planning/
│   └── codebase/                    # GSD analysis documents
├── docs/                            # Project milestone documents
├── start.sh                         # Starts both backend (port 8000) and frontend (port 3000)
└── .github/
    └── workflows/                   # CI configuration
```

## Directory Purposes

**`backend/app/core/`:**
- Purpose: Infrastructure wiring — config and database only
- Contains: `config.py` (all settings), `database.py` (engine + session factory)
- Key files: `backend/app/core/config.py`, `backend/app/core/database.py`

**`backend/app/models/`:**
- Purpose: SQLAlchemy ORM table definitions; the single source of truth for DB schema
- Contains: One file per domain entity; all re-exported from `__init__.py`
- Key files: `backend/app/models/stock.py` (central entity with all score columns)

**`backend/app/services/`:**
- Purpose: All business logic; each file is a self-contained analytical domain
- Contains: Singleton instances at module bottom (e.g., `scoring_engine = ScoringEngine()`)
- Note: Services open their own `AsyncSessionLocal()` contexts directly rather than using the `get_db()` dependency injection

**`backend/app/api/`:**
- Purpose: HTTP interface; one flat file with all routes
- Contains: Single `endpoints.py` with `router = APIRouter()`
- Note: All routes are in a single file; route grouping is done via comment banners

**`backend/scripts/`:**
- Purpose: One-off and maintenance scripts; not part of the running application
- Contains: DB seeding, manual refresh triggers, backtesting

**`frontend/src/app/`:**
- Purpose: Next.js App Router pages; each subdirectory is a route segment
- Contains: `page.tsx` files (all `'use client'`), co-located CSS Modules
- Pattern: Each page manages its own state with `useState`/`useEffect`; no global state manager

**`frontend/src/components/`:**
- Purpose: Shared UI primitives used across multiple pages
- Contains: `Sidebar.tsx` (global nav), `ScoreRing.tsx` (SVG score display), `StockHelpers.tsx` (formatters and badges)

**`frontend/src/lib/`:**
- Purpose: Non-UI utilities; currently only the API client
- Key files: `frontend/src/lib/api.ts`

## Key File Locations

**Entry Points:**
- `backend/app/main.py`: FastAPI app creation and lifespan hooks
- `frontend/src/app/layout.tsx`: Next.js root layout
- `frontend/src/app/page.tsx`: Dashboard (default route `/`)

**Configuration:**
- `backend/app/core/config.py`: All backend settings (DB URL, API keys, BIST100 list, weights)
- `frontend/next.config.ts`: Next.js/Turbopack config
- `frontend/src/lib/api.ts`: Frontend API base URL (`NEXT_PUBLIC_API_URL`)

**Core Logic:**
- `backend/app/services/scoring.py`: Weighted score aggregation
- `backend/app/services/causal.py`: Causal chain engine
- `backend/app/services/knowledge_graph.py`: In-memory economic graph
- `backend/app/api/endpoints.py`: All REST routes

**Data Models:**
- `backend/app/models/__init__.py`: All model exports
- `backend/app/models/stock.py`: Central `Stock` entity

## Naming Conventions

**Files (backend):**
- `snake_case.py` for all Python files
- Service files named after domain: `technical.py`, `fundamental.py`, `kap_parser.py`
- Model files named after entity: `stock.py`, `price.py`, `news.py`

**Files (frontend):**
- `PascalCase.tsx` for React components: `Sidebar.tsx`, `ScoreRing.tsx`
- `camelCase.ts` for utilities: `api.ts`
- CSS Modules co-located with component or page: `Sidebar.module.css`, `page.module.css`

**Python identifiers:**
- Classes: `PascalCase` (`ScoringEngine`, `KnowledgeGraph`, `CausalEngine`)
- Singletons: `snake_case` (`scoring_engine`, `causal_engine`, `knowledge_graph`)
- Constants/settings fields: `UPPER_SNAKE_CASE`

**TypeScript identifiers:**
- Interfaces: `PascalCase` (`StockSummary`, `CausalScenarioResult`)
- Functions and variables: `camelCase`
- API methods on the `api` object: `camelCase` verbs (`getDashboard`, `getStockDetail`, `triggerTCMBScan`)

## Where to Add New Code

**New analysis engine (e.g., new scoring dimension):**
- Implementation: `backend/app/services/<domain>.py` with a singleton at the bottom
- Register background job: `backend/app/main.py` lifespan block
- Add score column: `backend/app/models/stock.py`
- Expose via API: add route to `backend/app/api/endpoints.py`
- Add weight: `backend/app/core/config.py` `Settings` class

**New API endpoint:**
- Add route function to `backend/app/api/endpoints.py` on the existing `router`
- Add corresponding typed method to `frontend/src/lib/api.ts` `api` object
- Add matching interface type(s) in `frontend/src/lib/api.ts`

**New frontend page:**
- Create `frontend/src/app/<route-name>/page.tsx` with `'use client'` directive
- Add nav entry to `NAV_ITEMS` array in `frontend/src/components/Sidebar.tsx`
- Co-locate CSS Module as `frontend/src/app/<route-name>/<route-name>.module.css` if needed

**New shared UI component:**
- Place in `frontend/src/components/<ComponentName>.tsx`
- Co-locate CSS Module as `frontend/src/components/<ComponentName>.module.css`

**New data model:**
- Create `backend/app/models/<entity>.py` extending `Base`
- Re-export from `backend/app/models/__init__.py`
- Tables are auto-created by `conn.run_sync(Base.metadata.create_all)` in `main.py` lifespan

**Utilities / helpers:**
- Backend: no dedicated utils directory; place in the closest service file or create `backend/app/services/<util>.py`
- Frontend: `frontend/src/lib/` for non-component utilities

## Special Directories

**`backend/.venv/`:**
- Purpose: Python virtual environment
- Generated: Yes
- Committed: No

**`backend/alembic/`:**
- Purpose: Database migration infrastructure (Alembic)
- Generated: Partially (migration scripts would be generated)
- Committed: Yes (migration files); currently empty as schema is auto-created

**`backend/knowledge/`:**
- Purpose: Static knowledge files consumed by `KnowledgeGraph` service
- Generated: No
- Committed: Yes

**`frontend/.next/`:**
- Purpose: Next.js build output and dev server cache
- Generated: Yes
- Committed: No

**`frontend/node_modules/`:**
- Purpose: npm dependencies
- Generated: Yes
- Committed: No

**`.planning/codebase/`:**
- Purpose: GSD codebase analysis documents
- Generated: By GSD map-codebase command
- Committed: Yes (intended as living documentation)

---

*Structure analysis: 2026-04-16*
