<!-- GSD:project-start source:PROJECT.md -->
## Project

**Yatırım Asistanı**

Kişisel bir yatırım asistanı. BIST100 hisseleri, döviz ve altın için fırsat keşfi, portföy takibi ve AI destekli analiz sunar. Sadece bir araç değil — yatırımcıya hem karar desteği verir hem de her adımda neden öyle düşündüğünü açıklayarak borsa öğretir.

**Core Value:** Kullanıcının "bu hisseyi neden almalıyım?" sorusuna hem veriyle hem açıklamayla cevap vermek — karar kullanıcıda, anlayış asistanda.

### Constraints

- **Verimlilik**: AI API çağrıları yalnızca kullanıcı "Analiz Et" dediğinde yapılır
- **Kapsam**: BIST100 (100 hisse) — genişleme v2'ye bırakılır
- **Platform**: Web-first, responsive — native app yok
- **Dil**: Tamamen Türkçe
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.9 - Backend API, data collection, ML pipelines, scraping services
- TypeScript 5.x - Frontend React/Next.js components and API client
- CSS (globals.css, page.module.css) - Frontend styling
## Runtime
- Python 3.9.6 (pinned in CI via `actions/setup-python@v4` with `python-version: "3.9"`)
- Node.js 20.x (pinned via `nvm use 20` in `start.sh`; CI uses `node-version: "20.x"`)
- Backend: pip with `backend/requirements.txt`
- Frontend: npm; lockfile present (CI uses `npm ci`)
## Frameworks
- FastAPI 0.115.12 - Async REST API backend; main entry `backend/app/main.py`
- Uvicorn 0.34.2 (standard) - ASGI server, launched via `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- Next.js 16.2.3 - Frontend React framework; entry `frontend/src/app/layout.tsx`
- React 19.2.4 - UI rendering
- Starlette 0.46.2 - Underlying ASGI layer for FastAPI (CORS middleware)
- SQLAlchemy 2.0.40 (asyncio) - Async ORM and DB access; `backend/app/core/database.py`
- Alembic 1.15.2 - Schema migrations; config in `backend/alembic/`
- asyncpg 0.30.0 - Async PostgreSQL driver
- psycopg2-binary - Sync PostgreSQL driver for Alembic scripts
- scikit-learn 1.6.1 - Feature engineering, preprocessing (`StandardScaler`)
- XGBoost 2.1.4 - Primary ML model for price movement prediction; `backend/app/services/ml.py`
- TensorFlow 2.19.0 - LSTM model (60-day sliding window); config in `backend/app/core/config.py`
- SHAP 0.46.0 - ML explainability
- Transformers 4.51.3 (HuggingFace) - NLP model loading
- PyTorch 2.6.0 - Deep learning backend for Transformers
- vaderSentiment - Rule-based English sentiment analysis; used in `backend/app/services/macro_news.py`
- sentencepiece 0.2.0 - Tokenizer support
- yfinance 0.2.54 - Yahoo Finance market data; used extensively across `data_collector.py`, `fundamental.py`, `sentiment.py`, `macro_news.py`
- pandas 2.2.3 - DataFrame-based data processing
- numpy 1.26.4 - Numerical computation
- ta 0.11.0 - Technical analysis indicators (RSI, MACD, Bollinger Bands, etc.)
- requests 2.32.3 - Sync HTTP calls
- aiohttp 3.11.18 - Async HTTP calls (TCMB, TUIK scrapers)
- httpx 0.28.1 - Async HTTP client
- beautifulsoup4 4.13.4 - HTML scraping (TCMB, TUIK adapters)
- feedparser 6.0.11 - RSS feed parsing (KAP announcements)
- lxml 5.4.0 - XML/HTML parser backend for BeautifulSoup
- APScheduler 3.11.0 - Background job scheduler; registered in `backend/app/main.py` lifespan
- framer-motion 12.38.0 - Animation library
- lightweight-charts 5.1.0 - TradingView-compatible candlestick/price charts
- @heroicons/react 2.2.0 - SVG icon set
- pydantic 2.11.1 - Data models and validation
- pydantic-settings 2.8.1 - Settings management from `.env`; `backend/app/core/config.py`
- python-dotenv 1.1.0 - `.env` file loading
- python-multipart 0.0.20 - Form data support for FastAPI
- ESLint 9.x with `eslint-config-next` - Frontend linting; config in `frontend/eslint.config.mjs`
- Next.js Turbopack - Dev bundler; enabled in `frontend/next.config.ts`
- ruff 0.15.10 - Python linter; cache at `backend/.ruff_cache/`
## Key Dependencies
- `yfinance==0.2.54` - Primary market data source for prices, fundamentals, news; any API change breaks data ingestion
- `fastapi==0.115.12` - All 30+ REST endpoints; upgrade requires endpoint compatibility check
- `sqlalchemy[asyncio]==2.0.40` - All DB reads/writes are async; sync and async engines both required
- `xgboost==2.1.4` - ML prediction pipeline; requires `libomp` system library (guarded by try/except in `ml.py`)
- `tensorflow==2.19.0` - LSTM model; large dependency (~600MB), loaded for 60-day price prediction
- `transformers==4.51.3` + `torch==2.6.0` - NLP pipeline; very large combined size
- `apscheduler==3.11.0` - Drives all autonomous background jobs (KAP every 5min, TCMB every 2h, TUIK daily 9:00, audit 18:05, portfolio 18:15)
- `asyncpg==0.30.0` - PostgreSQL async driver; must match SQLAlchemy asyncio engine
- `alembic==1.15.2` - DB migrations; `psycopg2-binary` required for sync Alembic operations
## Configuration
- Settings class in `backend/app/core/config.py` using `pydantic-settings`
- Loaded from `.env` file in backend root (not committed)
- Key settings required at runtime:
- Frontend reads `NEXT_PUBLIC_API_URL` env var; defaults to `http://localhost:8000/api`
- Frontend: `frontend/next.config.ts` (Turbopack enabled with `root: process.cwd()`)
- Backend: no separate build step; runs directly with Uvicorn
- Migrations: `backend/alembic/` directory with Alembic configuration
## Platform Requirements
- Python 3.9 with virtual environment at `backend/.venv/`
- Node.js 20 (managed via nvm)
- PostgreSQL database named `stockanalist` on localhost:5432
- Start script: `./start.sh` launches both services
- No deployment platform detected (CI pipeline builds but does not deploy)
- CI/CD: GitHub Actions at `.github/workflows/main.yml` (test backend + build frontend on push/PR to main)
- Backend target: Ubuntu-compatible Linux (CI uses `ubuntu-latest`)
- No Docker, no containerization detected
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Patterns
- React components: PascalCase — `ScoreRing.tsx`, `StockHelpers.tsx`, `Sidebar.tsx`
- CSS modules co-located with component: `Sidebar.module.css`, `page.module.css`
- Next.js pages: `page.tsx` inside route directories (App Router)
- Python services: snake_case — `data_collector.py`, `scoring.py`, `kap_parser.py`
- Python models: snake_case — `stock.py`, `price.py`, `model_portfolio.py`
- TypeScript: camelCase — `loadData()`, `apiFetch()`, `formatPrice()`, `formatVolume()`
- Python: snake_case — `calculate_indicators()`, `update_all_scores()`, `run_kap_scan()`
- Python background tasks: `background_<action>()` — `background_macro_scan()`, `background_kap_scan()`
- TypeScript: camelCase — `allStocks`, `filterBist30`, `sortBy`
- Python: snake_case — `async_engine`, `causal_engine`, `scoring_engine`
- TypeScript: PascalCase interfaces — `StockSummary`, `DashboardData`, `FetchOptions`
- Python: PascalCase classes — `ScoringEngine`, `TechnicalAnalysisEngine`, `DataCollector`
- Python dataclasses: PascalCase — `CausalScenario`, `StockImpact`
- Python Pydantic models: PascalCase — `PortfolioCreate`, `Settings`
- TypeScript: SCREAMING_SNAKE_CASE for config records — `REC_CONFIG`, `NAV_ITEMS`
- Python: SCREAMING_SNAKE_CASE for class constants — `BASE_WEIGHTS`, `DEFAULT_SCORE`
## Code Style
- TypeScript/TSX: 2-space indentation (inferred from files)
- Python: 4-space indentation (PEP 8 standard)
- No Prettier config present — relies on editor defaults and ESLint
- Tool: ESLint 9 with `eslint-config-next/core-web-vitals` + `eslint-config-next/typescript`
- Config: `frontend/eslint.config.mjs` (flat config format)
- TypeScript strict mode enabled in `frontend/tsconfig.json`: `"strict": true`
- No explicit linter config detected (no `.flake8`, `pyproject.toml`, or `setup.cfg`)
- Type hints used throughout but inconsistently (some `Any` usage in `fundamental.py`)
## Import Organization
- `@/*` maps to `frontend/src/*` (configured in `frontend/tsconfig.json`)
- Use `@/components/`, `@/lib/`, `@/app/` — never relative `../../`
- Module-level `logger = logging.getLogger(__name__)` always defined after imports
## Error Handling
- API calls wrapped in `try/catch` with `finally` for loading state
- Error state stored as `string | null` and displayed in UI:
- Silent catch used in non-critical paths: `catch { /* */ }` (seen in `stocks/page.tsx`)
- API client throws `new Error(error.detail || \`HTTP ${res.status}\`)` on non-OK responses
- FastAPI routes raise `HTTPException` for client errors:
- Background tasks catch all exceptions and log, never re-raise (to keep scheduler alive):
- Database session error handling via `get_db()` dependency with rollback on exception
- Inline `import logging; logging.getLogger(__name__).error(...)` used in some endpoints (inconsistent)
## Logging
- Module-level logger: `logger = logging.getLogger(__name__)` at top of each service file
- Background task logs use emoji prefixes for visual scanning: `"🔴 TETİKLENDİ:"`, `"📊 TETİKLENDİ:"`
- Info for lifecycle events, error for caught exceptions, warning for edge cases
- SQLAlchemy engine log suppressed: `logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)`
- No structured logging (JSON) — plain text format
- No logging framework — errors stored in React state and shown in UI
## Comments
- Module docstrings always present at file top: triple-quoted with purpose description
- Class/method docstrings for complex logic (e.g., `ScoringEngine`, `calculate_overall_score`)
- Inline section dividers using box-drawing or dashes: `# ─── SECTION NAME ───`
- Turkish-language inline comments common throughout codebase
- `# TODO` used sparingly — only 2 found in `event_fusion.py`
- JSDoc not used — no `/** */` blocks in frontend code
- Section dividers with em-dashes: `// ── Sub Components ──`
- Minimal inline comments; code is largely self-documenting via TypeScript types
## Function Design
- Pages use a single `loadData()` async function called from `useEffect`
- Helper functions defined as standalone named functions at bottom of page files (not exported)
- Pure formatting helpers exported from `StockHelpers.tsx`: `formatPrice()`, `formatVolume()`, `formatMarketCap()`, `formatPercentage()`
- React components receive strongly-typed props interfaces
- Service classes use engine/singleton pattern: `scoring_engine = ScoringEngine()` at module bottom
- Private methods prefixed with `_`: `_resolve_weights()`, `_safe_float()`
- Async functions for all DB operations; sync functions for pure computation
## Module Design
- Pages: default export only (`export default function DashboardPage()`)
- Components: default export for main component + named exports for helpers (e.g., `StockHelpers.tsx`)
- API client: named interface exports + `export const api = {...}` + `export default api`
- No barrel `index.ts` files detected
- Service singletons instantiated at module bottom and imported by name:
- Pydantic models in `app/models/` imported directly by path
- `app/core/config.py` exports `settings = Settings()` singleton
## Client Directive Usage (Next.js)
- `'use client'` placed at top of every component/page that uses React hooks or browser APIs
- All page files and all components in `src/components/` use `'use client'`
- No Server Components with data fetching observed — all data loading is client-side via `useEffect`
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- Python FastAPI backend with async PostgreSQL, accessed exclusively via REST
- Next.js 15 frontend (App Router, all pages are `'use client'` React hooks)
- Autonomous background scheduler (APScheduler) drives all data ingestion pipelines
- Domain logic is split into specialized singleton service engines; no shared service layer on the frontend
## Layers
- Purpose: Centralized settings loaded from environment; single source of truth for all constants including BIST100 symbols, API keys, weights, and source catalog
- Location: `backend/app/core/config.py`
- Contains: `Settings` (pydantic-settings `BaseSettings` subclass), singleton `settings` object
- Depends on: `.env` file, environment variables
- Used by: every backend service and API layer
- Purpose: Async SQLAlchemy engine, session factory, and declarative base
- Location: `backend/app/core/database.py`
- Contains: `async_engine`, `sync_engine` (for Alembic), `AsyncSessionLocal`, `Base`, `get_db()` dependency, `init_db()`
- Depends on: `settings.DATABASE_URL`
- Used by: all service singletons and endpoint handlers (direct `AsyncSessionLocal()` context managers, not injected `get_db()` in most services)
- Purpose: SQLAlchemy ORM table definitions; data shape is authoritative here
- Location: `backend/app/models/`
- Contains: `Stock`, `PriceHistory`, `CommodityPrice`, `Fundamental`, `NewsItem`, `Recommendation`, `PortfolioItem`, `GeopoliticalEvent`, `MacroIndicator`, `CausalChainLog`, `ModelPortfolioHistory`
- Depends on: `Base` from database layer
- Used by: service layer, API endpoints
- Purpose: All business logic — data collection, technical/fundamental/ML/causal/sentiment analysis, scoring, portfolio optimization
- Location: `backend/app/services/`
- Contains: 20 specialized modules, each exposes a singleton engine (e.g., `scoring_engine`, `technical_engine`, `causal_engine`)
- Depends on: models, core config, external APIs (yfinance, KAP RSS, TCMB, TUIK, DeepSeek LLM)
- Used by: API endpoints, APScheduler background tasks
- Purpose: Single FastAPI router exposing all REST endpoints consumed by the frontend
- Location: `backend/app/api/endpoints.py`
- Contains: One `APIRouter` with all routes (portfolio, model-portfolio, stocks, rankings, causal, scoring, sectors, health, macro, intelligence, correlation)
- Depends on: service singletons, models, `AsyncSessionLocal`
- Used by: `main.py` which mounts it at `/api`
- Purpose: Autonomous background tasks that run data ingestion and AI processes on schedule
- Location: `backend/app/main.py` (lifespan context manager)
- Contains: `AsyncIOScheduler` with 8 jobs — macro scan (1h), KAP scan (5 min), TCMB scan (2h), TUIK scan (weekdays 9:00), event fusion (1h), dynamic correlation (Monday 9:30), AI audit (weekdays 18:05), model portfolio generation (weekdays 18:15)
- Depends on: service singletons
- Used by: invoked automatically on startup
- Purpose: Single typed wrapper around all backend REST calls; type contracts defined here
- Location: `frontend/src/lib/api.ts`
- Contains: `apiFetch<T>()` generic, all interface types (`StockSummary`, `DashboardData`, `CausalScenarioResult`, `PortfolioResponse`, etc.), exported `api` object with named methods
- Depends on: `NEXT_PUBLIC_API_URL` env var (default: `http://localhost:8000/api`)
- Used by: all frontend page components
- Purpose: Next.js App Router pages and reusable components; all pages are client components
- Location: `frontend/src/app/` (pages), `frontend/src/components/` (shared UI)
- Contains: pages for Dashboard, Intelligence, Faz9 (Macro), Stocks, Stock Detail, Causal, Model Portfolio, Sectors, Rankings, Portfolio
- Depends on: `api` client in `frontend/src/lib/api.ts`
- Used by: end users via browser
## Data Flow
## Key Abstractions
- Purpose: Weighted aggregation of sub-scores into a single actionable recommendation
- Pattern: Singleton (`scoring_engine`); methods are `calculate_overall_score(stock)` and `update_all_scores()`
- Purpose: Graph traversal that answers "if X changes → which stocks are affected and how?"
- Pattern: `KnowledgeGraph` builds an in-memory directed graph at startup; `CausalEngine` holds a reference to it and performs BFS-style propagation
- Purpose: Orchestrates all external data pulls (yfinance prices, fundamentals, commodities, currencies, indices)
- Pattern: Singleton; called from scripts and scheduler tasks
- Purpose: Single point of truth for all typed API contracts between frontend and backend
- Pattern: Plain object of named async functions; all types defined as exported interfaces in the same file
## Entry Points
- Location: `backend/app/main.py`
- Triggers: `uvicorn app.main:app` (see `start.sh`)
- Responsibilities: Creates FastAPI app, attaches CORS middleware, mounts `router` at `/api`, runs lifespan (DB init, scheduler start)
- Location: `frontend/src/app/layout.tsx` (root layout), `frontend/src/app/page.tsx` (Dashboard)
- Triggers: `npm run dev` via Next.js (see `start.sh`)
- Responsibilities: `layout.tsx` sets HTML lang and global metadata; each page component is self-contained with its own data loading
- `backend/scripts/initial_load.py` — seed BIST100 stocks into database
- `backend/scripts/update_ai.py` — manual AI score refresh
- `backend/scripts/update_fundamentals.py` — manual fundamentals refresh
- `backend/scripts/backtester.py` — historical backtesting
## Error Handling
- All background scheduler functions wrap service calls in `try/except Exception as e: logging.error(...)`
- Frontend `apiFetch<T>` throws on non-OK HTTP; page components catch in a top-level `try/catch` and set an `error` state for display
- Services that depend on optional packages (XGBoost, feedparser) guard with `try/except ImportError` at module level and degrade gracefully
## Cross-Cutting Concerns
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
