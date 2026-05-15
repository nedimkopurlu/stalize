# Phase 50 — Market Regime Engine

## Goal

Implement a daily BIST100 market regime detector (Boğa/Ayı/Yatay/Volatil) using ADX+EMA200+ATR rule-based logic on USD-adjusted XU100.IS data. Surface the regime as a badge on the dashboard and stock detail page.

## Requirements

- **REJ-01** — System automatically detects daily market regime for BIST100 (Boğa/Ayı/Yatay/Volatil): ADX+EMA200+ATR rule-based on USD-adjusted XU100.IS. Runs daily at 18:30 via APScheduler. Persisted in `market_regime` table.
- **REJ-02** — Current market regime shown as a regime badge on the dashboard (after summary stats) and on the stock detail page (hero section).

## Locked Decisions

All decisions below are autonomous — no user input needed.

### Backend (REJ-01)

**Regime model:** New `MarketRegime` SQLAlchemy model in `backend/app/models/market_regime.py`.
- Columns: `id INTEGER PK`, `date DATE UNIQUE`, `regime VARCHAR(20)`, `adx FLOAT`, `ema200 FLOAT`, `atr FLOAT`, `created_at TIMESTAMP`
- Upsert pattern: delete today's row if exists, then insert fresh — avoids ON CONFLICT complexity with SQLAlchemy asyncio.

**Detection logic** (`backend/app/services/market_regime.py`):
- Fetch XU100.IS last 300 trading days via yfinance (`yf.download("XU100.IS", period="300d", interval="1d")`)
- Fetch USDTRY rate (`yf.download("USDTRY=X", period="300d", interval="1d")`)
- Align on date, compute `usd_close = xu100_close / usdtry_close`
- Use `ta` library:
  - `ta.trend.ADXIndicator(high, low, close, window=14)` — `.adx()` series
  - `ta.trend.EMAIndicator(close, window=200)` — `.ema_indicator()` series
  - `ta.volatility.AverageTrueRange(high, low, close, window=14)` — `.average_true_range()` series
- Take last row of each series for today's values
- Classification (in priority order):
  1. **Volatil**: `atr_ratio >= 0.02` (where `atr_ratio = atr / usd_close`)
  2. **Ayı**: `usd_close < ema200 AND adx > 25`
  3. **Boğa**: `usd_close > ema200 AND adx > 25`
  4. **Yatay**: default (ADX <= 25, no strong directional signal)

**API endpoint:** `GET /api/market-regime` → `{"regime": "Boğa", "date": "2026-05-15", "adx": 28.4, "ema200": 1.23, "atr": 0.024}`
- Returns latest row from `market_regime` table; 404 if no data yet.
- Router: add to `backend/app/api/market.py` (already imported in `main.py` as `market.router`).

**Scheduler:** `background_market_regime_update` function in `main.py`, cron job at `18:30 Europe/Istanbul`, weekdays only.

**Migration:** `010_add_market_regime_table.py` — create `market_regime` table with idempotent `inspector.get_table_names()` check.

### Frontend (REJ-02)

**API type:** `MarketRegimeResponse` interface in `frontend/src/lib/api.ts`; method `api.getMarketRegime()`.

**Dashboard badge:** Add `RegimeBadge` component inline in `frontend/src/app/page.tsx`. Placed inside the `heroSection`/`marketFacts` area after the existing `Fact` components. Badge shows regime name + colored dot.

**Stock detail badge:** Add `RegimeBadge` in `frontend/src/app/stocks/[symbol]/page.tsx` hero section, near the score summary.

**Badge colors (CSS custom properties already in globals.css):**
- Boğa → `var(--accent-green)` (green)
- Ayı → `var(--accent-red)` (red)
- Yatay → `var(--text-muted)` (gray)
- Volatil → `#f59e0b` (amber — inline style, not a CSS variable)

**State loading:** `api.getMarketRegime()` called in `load()` on both pages; stored in `regime` state; error silently swallowed (`.catch(() => null)`).

## Codebase Patterns to Follow

- New model file in `backend/app/models/`, imported and exported in `backend/app/models/__init__.py`
- Service singleton at module bottom: `market_regime_engine = MarketRegimeEngine()`
- Background job function in `main.py`, added to scheduler in `lifespan`
- Cron jobs use `"cron"` trigger with `day_of_week="mon-fri"`, `timezone="Europe/Istanbul"`, `max_instances=1`, `misfire_grace_time=300`
- API endpoint added to existing `market.router` (not a new router file)
- All data loading in frontend pages via `useCallback` + `useEffect`, silent catch
- CSS modules co-located: badge styles added to `page.module.css` in each page directory
