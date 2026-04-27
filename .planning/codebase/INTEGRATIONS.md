# External Integrations

**Analysis Date:** 2026-04-16

## APIs & External Services

**LLM / AI:**
- DeepSeek API - Sentiment and causal impact analysis on financial news
  - SDK/Client: `openai` Python package with `base_url="https://api.deepseek.com/v1"`
  - Auth: `DEEPSEEK_API_KEY` env var
  - Used in: `backend/app/services/llm_sentiment.py` (`DeepSeekSentimentService`)
  - Model: `deepseek-chat` (configurable via `LLM_MODEL` setting)
  - Behavior: feature is disabled when key is absent (`LLM_ENABLED = False`); mock values returned

- OpenAI API - Alternative LLM provider (optional)
  - SDK/Client: `openai` Python package
  - Auth: `OPENAI_API_KEY` env var
  - Same service class as DeepSeek; client swapped by key presence

**Market Data:**
- Yahoo Finance (yfinance) - BIST100 stock prices, fundamentals, commodities, FX, indices, news
  - SDK/Client: `yfinance==0.2.54`
  - Auth: None (unauthenticated, rate-limited)
  - Used in: `backend/app/services/data_collector.py`, `fundamental.py`, `sentiment.py`, `macro_news.py`
  - Symbols accessed: `{TICKER}.IS` for BIST stocks, commodity futures (`BZ=F`, `GC=F`, etc.), FX pairs (`USDTRY=X`), indices (`^GSPC`, `XU100.IS`), bond yields (`^TNX`)

**Turkish Official Data Sources (Web Scraping):**
- KAP (Kamuyu Aydınlatma Platformu) - Official corporate disclosures RSS feed
  - SDK/Client: `feedparser==6.0.11`
  - Auth: None (public RSS)
  - URL: `https://www.kap.org.tr/tr/rss/bildirimler` (primary), `https://www.kap.org.tr/en/rss` (backup)
  - Scan interval: every 5 minutes (configurable via `KAP_SCAN_INTERVAL_MIN`)
  - Used in: `backend/app/services/kap_parser.py`

- TCMB (Türkiye Cumhuriyet Merkez Bankası) - Central Bank monetary policy data
  - SDK/Client: `aiohttp==3.11.18` + `beautifulsoup4==4.13.4`
  - Auth: None (public web scraping)
  - Base URL: `https://www.tcmb.gov.tr`
  - Data fetched: policy rate, FX reserves, monetary policy announcements
  - Scan interval: every 2 hours (APScheduler)
  - Used in: `backend/app/services/tcmb_adapter.py`

- TUIK (Türkiye İstatistik Kurumu) - National statistics (CPI, unemployment, industrial output)
  - SDK/Client: `aiohttp==3.11.18` + `beautifulsoup4==4.13.4`
  - Auth: None (public web scraping)
  - Base URL: `https://www.tuik.gov.tr`
  - Data fetched: CPI/inflation, industrial production index, unemployment rate, capacity utilization, trade balance
  - Scan interval: daily at 09:00 Mon-Fri (APScheduler cron)
  - Used in: `backend/app/services/tuik_adapter.py`

**Financial News (Monitored but not directly integrated via SDK):**
- The `SOURCE_CATALOG` in `backend/app/core/config.py` lists 34 financial news sources including Bloomberg, Reuters, Financial Times, Bloomberg HT, Ekonomim, Fintables, etc. These are priority-ranked but fetched via yfinance news API or web scraping, not via dedicated SDKs.

## Data Storage

**Databases:**
- PostgreSQL
  - Async connection: `postgresql+asyncpg://localhost:5432/stockanalist`
  - Sync connection (Alembic): `postgresql+psycopg2://localhost:5432/stockanalist`
  - Connection env var: `DATABASE_URL` and `DATABASE_SYNC_URL`
  - Client: SQLAlchemy 2.0 (async ORM); `backend/app/core/database.py`
  - Pool: 20 connections (async), 5 connections (sync), `pool_pre_ping=True`
  - Models: `Stock`, `PriceHistory`, `CommodityPrice`, `Fundamental`, `NewsItem`, `PortfolioItem`, `ModelPortfolio`, `Recommendation`, `Geopolitics` in `backend/app/models/`

**File Storage:**
- Local filesystem only
  - ML models: `backend/ml_models/` directory (path: `backend/app/core/config.py` → `ML_MODEL_DIR`)
  - Knowledge graph: `backend/knowledge/` directory (path: `backend/app/core/config.py` → `KNOWLEDGE_DIR`)

**Caching:**
- In-memory only; yfinance has a `YFINANCE_CACHE_TTL=3600` config value but no external cache store (no Redis detected)

## Authentication & Identity

**Auth Provider:**
- None — no user authentication system detected
- API is open (CORS `allow_origins=["*"]` in `backend/app/main.py`)
- No JWT, session, or OAuth integration found

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry, Datadog, or similar detected)

**Logs:**
- Python `logging` module throughout backend services
- Log level: `sqlalchemy.engine` set to WARNING in production context (`backend/app/main.py`)
- No structured log shipping or aggregation configured

## CI/CD & Deployment

**Hosting:**
- Not determined — no deployment target configured in CI

**CI Pipeline:**
- GitHub Actions at `.github/workflows/main.yml`
- Triggers: push and PR to `main` branch
- Jobs:
  - `test-backend`: sets up Python 3.9, installs requirements + pytest + httpx, runs echo placeholder (tests not implemented)
  - `build-frontend`: sets up Node 20, runs `npm ci` and `npm run build`
- No deployment step present

## Environment Configuration

**Required env vars (backend):**
- `DATABASE_URL` — async PostgreSQL DSN (default provided but DB must exist)
- `DATABASE_SYNC_URL` — sync PostgreSQL DSN for Alembic
- `DEEPSEEK_API_KEY` — optional; enables LLM sentiment analysis
- `OPENAI_API_KEY` — optional; alternative LLM provider

**Required env vars (frontend):**
- `NEXT_PUBLIC_API_URL` — backend base URL (defaults to `http://localhost:8000/api`)

**Secrets location:**
- Backend `.env` file in `backend/` root directory (loaded by pydantic-settings; not committed to git)
- Frontend `.env.local` or environment injection at build time for `NEXT_PUBLIC_API_URL`

## Webhooks & Callbacks

**Incoming:**
- None detected

**Outgoing:**
- None detected

## Scheduled Background Jobs

All jobs are registered in `backend/app/main.py` via APScheduler:

| Job | Schedule | Service |
|-----|----------|---------|
| Macro news scan | Every 1 hour | `backend/app/services/causal.py` |
| KAP scan | Every 5 minutes | `backend/app/services/kap_parser.py` |
| TCMB data scan | Every 2 hours | `backend/app/services/tcmb_adapter.py` |
| TUIK data scan | Mon-Fri 09:00 | `backend/app/services/tuik_adapter.py` |
| Event fusion pipeline | Every 1 hour | `backend/app/services/event_fusion.py` |
| Dynamic correlation matrix | Monday 09:30 | `backend/app/services/dynamic_correlation.py` |
| AI audit and learning | Mon-Fri 18:05 | `backend/app/services/performance_monitor.py` |
| Model portfolio generation | Mon-Fri 18:15 | `backend/app/services/portfolio_optimizer.py` |

---

*Integration audit: 2026-04-16*
