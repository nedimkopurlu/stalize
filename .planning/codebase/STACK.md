# Technology Stack

**Analysis Date:** 2026-04-16

## Languages

**Primary:**
- Python 3.9 - Backend API, data collection, ML pipelines, scraping services
- TypeScript 5.x - Frontend React/Next.js components and API client

**Secondary:**
- CSS (globals.css, page.module.css) - Frontend styling

## Runtime

**Environment:**
- Python 3.9.6 (pinned in CI via `actions/setup-python@v4` with `python-version: "3.9"`)
- Node.js 20.x (pinned via `nvm use 20` in `start.sh`; CI uses `node-version: "20.x"`)

**Package Manager:**
- Backend: pip with `backend/requirements.txt`
- Frontend: npm; lockfile present (CI uses `npm ci`)

## Frameworks

**Core:**
- FastAPI 0.115.12 - Async REST API backend; main entry `backend/app/main.py`
- Uvicorn 0.34.2 (standard) - ASGI server, launched via `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- Next.js 16.2.3 - Frontend React framework; entry `frontend/src/app/layout.tsx`
- React 19.2.4 - UI rendering
- Starlette 0.46.2 - Underlying ASGI layer for FastAPI (CORS middleware)

**Data / ORM:**
- SQLAlchemy 2.0.40 (asyncio) - Async ORM and DB access; `backend/app/core/database.py`
- Alembic 1.15.2 - Schema migrations; config in `backend/alembic/`
- asyncpg 0.30.0 - Async PostgreSQL driver
- psycopg2-binary - Sync PostgreSQL driver for Alembic scripts

**Machine Learning:**
- scikit-learn 1.6.1 - Feature engineering, preprocessing (`StandardScaler`)
- XGBoost 2.1.4 - Primary ML model for price movement prediction; `backend/app/services/ml.py`
- TensorFlow 2.19.0 - LSTM model (60-day sliding window); config in `backend/app/core/config.py`
- SHAP 0.46.0 - ML explainability

**NLP / Sentiment:**
- Transformers 4.51.3 (HuggingFace) - NLP model loading
- PyTorch 2.6.0 - Deep learning backend for Transformers
- vaderSentiment - Rule-based English sentiment analysis; used in `backend/app/services/macro_news.py`
- sentencepiece 0.2.0 - Tokenizer support

**Data Collection:**
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

**Scheduling:**
- APScheduler 3.11.0 - Background job scheduler; registered in `backend/app/main.py` lifespan

**Frontend UI:**
- framer-motion 12.38.0 - Animation library
- lightweight-charts 5.1.0 - TradingView-compatible candlestick/price charts
- @heroicons/react 2.2.0 - SVG icon set

**Configuration / Utilities:**
- pydantic 2.11.1 - Data models and validation
- pydantic-settings 2.8.1 - Settings management from `.env`; `backend/app/core/config.py`
- python-dotenv 1.1.0 - `.env` file loading
- python-multipart 0.0.20 - Form data support for FastAPI

**Build / Dev:**
- ESLint 9.x with `eslint-config-next` - Frontend linting; config in `frontend/eslint.config.mjs`
- Next.js Turbopack - Dev bundler; enabled in `frontend/next.config.ts`
- ruff 0.15.10 - Python linter; cache at `backend/.ruff_cache/`

## Key Dependencies

**Critical:**
- `yfinance==0.2.54` - Primary market data source for prices, fundamentals, news; any API change breaks data ingestion
- `fastapi==0.115.12` - All 30+ REST endpoints; upgrade requires endpoint compatibility check
- `sqlalchemy[asyncio]==2.0.40` - All DB reads/writes are async; sync and async engines both required
- `xgboost==2.1.4` - ML prediction pipeline; requires `libomp` system library (guarded by try/except in `ml.py`)
- `tensorflow==2.19.0` - LSTM model; large dependency (~600MB), loaded for 60-day price prediction
- `transformers==4.51.3` + `torch==2.6.0` - NLP pipeline; very large combined size

**Infrastructure:**
- `apscheduler==3.11.0` - Drives all autonomous background jobs (KAP every 5min, TCMB every 2h, TUIK daily 9:00, audit 18:05, portfolio 18:15)
- `asyncpg==0.30.0` - PostgreSQL async driver; must match SQLAlchemy asyncio engine
- `alembic==1.15.2` - DB migrations; `psycopg2-binary` required for sync Alembic operations

## Configuration

**Environment:**
- Settings class in `backend/app/core/config.py` using `pydantic-settings`
- Loaded from `.env` file in backend root (not committed)
- Key settings required at runtime:
  - `DATABASE_URL` — defaults to `postgresql+asyncpg://localhost:5432/stockanalist`
  - `DATABASE_SYNC_URL` — defaults to `postgresql+psycopg2://localhost:5432/stockanalist`
  - `DEEPSEEK_API_KEY` — optional; LLM features disabled when absent
  - `OPENAI_API_KEY` — optional; alternative LLM provider
- Frontend reads `NEXT_PUBLIC_API_URL` env var; defaults to `http://localhost:8000/api`

**Build:**
- Frontend: `frontend/next.config.ts` (Turbopack enabled with `root: process.cwd()`)
- Backend: no separate build step; runs directly with Uvicorn
- Migrations: `backend/alembic/` directory with Alembic configuration

## Platform Requirements

**Development:**
- Python 3.9 with virtual environment at `backend/.venv/`
- Node.js 20 (managed via nvm)
- PostgreSQL database named `stockanalist` on localhost:5432
- Start script: `./start.sh` launches both services

**Production:**
- No deployment platform detected (CI pipeline builds but does not deploy)
- CI/CD: GitHub Actions at `.github/workflows/main.yml` (test backend + build frontend on push/PR to main)
- Backend target: Ubuntu-compatible Linux (CI uses `ubuntu-latest`)
- No Docker, no containerization detected

---

*Stack analysis: 2026-04-16*
