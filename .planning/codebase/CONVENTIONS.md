# Coding Conventions

**Analysis Date:** 2026-04-16

## Naming Patterns

**Files:**
- React components: PascalCase — `ScoreRing.tsx`, `StockHelpers.tsx`, `Sidebar.tsx`
- CSS modules co-located with component: `Sidebar.module.css`, `page.module.css`
- Next.js pages: `page.tsx` inside route directories (App Router)
- Python services: snake_case — `data_collector.py`, `scoring.py`, `kap_parser.py`
- Python models: snake_case — `stock.py`, `price.py`, `model_portfolio.py`

**Functions/Methods:**
- TypeScript: camelCase — `loadData()`, `apiFetch()`, `formatPrice()`, `formatVolume()`
- Python: snake_case — `calculate_indicators()`, `update_all_scores()`, `run_kap_scan()`
- Python background tasks: `background_<action>()` — `background_macro_scan()`, `background_kap_scan()`

**Variables:**
- TypeScript: camelCase — `allStocks`, `filterBist30`, `sortBy`
- Python: snake_case — `async_engine`, `causal_engine`, `scoring_engine`

**Types/Interfaces:**
- TypeScript: PascalCase interfaces — `StockSummary`, `DashboardData`, `FetchOptions`
- Python: PascalCase classes — `ScoringEngine`, `TechnicalAnalysisEngine`, `DataCollector`
- Python dataclasses: PascalCase — `CausalScenario`, `StockImpact`
- Python Pydantic models: PascalCase — `PortfolioCreate`, `Settings`

**Constants:**
- TypeScript: SCREAMING_SNAKE_CASE for config records — `REC_CONFIG`, `NAV_ITEMS`
- Python: SCREAMING_SNAKE_CASE for class constants — `BASE_WEIGHTS`, `DEFAULT_SCORE`

## Code Style

**Formatting:**
- TypeScript/TSX: 2-space indentation (inferred from files)
- Python: 4-space indentation (PEP 8 standard)
- No Prettier config present — relies on editor defaults and ESLint

**Linting (Frontend):**
- Tool: ESLint 9 with `eslint-config-next/core-web-vitals` + `eslint-config-next/typescript`
- Config: `frontend/eslint.config.mjs` (flat config format)
- TypeScript strict mode enabled in `frontend/tsconfig.json`: `"strict": true`

**Python:**
- No explicit linter config detected (no `.flake8`, `pyproject.toml`, or `setup.cfg`)
- Type hints used throughout but inconsistently (some `Any` usage in `fundamental.py`)

## Import Organization

**TypeScript (observed pattern):**
1. `'use client'` directive (top of file when needed)
2. React imports — `import React, { useEffect, useState } from 'react'`
3. Next.js imports — `import Link from 'next/link'`, `import { usePathname } from 'next/navigation'`
4. Internal components — `import Sidebar from '@/components/Sidebar'`
5. Internal lib/api — `import api, { StockSummary } from '@/lib/api'`
6. CSS modules — `import styles from './page.module.css'`

**Path Aliases:**
- `@/*` maps to `frontend/src/*` (configured in `frontend/tsconfig.json`)
- Use `@/components/`, `@/lib/`, `@/app/` — never relative `../../`

**Python (observed pattern):**
1. Standard library imports
2. Third-party imports (fastapi, sqlalchemy, pandas, etc.)
3. Internal app imports (`from app.core...`, `from app.models...`, `from app.services...`)
- Module-level `logger = logging.getLogger(__name__)` always defined after imports

## Error Handling

**TypeScript (Frontend):**
- API calls wrapped in `try/catch` with `finally` for loading state
- Error state stored as `string | null` and displayed in UI:
  ```typescript
  try {
    const result = await api.getDashboard();
    setData(result);
  } catch (err) {
    setError(err instanceof Error ? err.message : 'API bağlantı hatası');
  } finally {
    setLoading(false);
  }
  ```
- Silent catch used in non-critical paths: `catch { /* */ }` (seen in `stocks/page.tsx`)
- API client throws `new Error(error.detail || \`HTTP ${res.status}\`)` on non-OK responses

**Python (Backend):**
- FastAPI routes raise `HTTPException` for client errors:
  ```python
  if not stock:
      raise HTTPException(status_code=404, detail="Hisse senedi bulunamadı.")
  ```
- Background tasks catch all exceptions and log, never re-raise (to keep scheduler alive):
  ```python
  try:
      await causal_engine.run_realtime_scenarios()
  except Exception as e:
      logging.error(f"Arkaplan Makro Tarama Hatası: {e}")
  ```
- Database session error handling via `get_db()` dependency with rollback on exception
- Inline `import logging; logging.getLogger(__name__).error(...)` used in some endpoints (inconsistent)

## Logging

**Framework:** Python `logging` module (standard library)

**Patterns:**
- Module-level logger: `logger = logging.getLogger(__name__)` at top of each service file
- Background task logs use emoji prefixes for visual scanning: `"🔴 TETİKLENDİ:"`, `"📊 TETİKLENDİ:"`
- Info for lifecycle events, error for caught exceptions, warning for edge cases
- SQLAlchemy engine log suppressed: `logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)`
- No structured logging (JSON) — plain text format

**Frontend:**
- No logging framework — errors stored in React state and shown in UI

## Comments

**Python:**
- Module docstrings always present at file top: triple-quoted with purpose description
- Class/method docstrings for complex logic (e.g., `ScoringEngine`, `calculate_overall_score`)
- Inline section dividers using box-drawing or dashes: `# ─── SECTION NAME ───`
- Turkish-language inline comments common throughout codebase
- `# TODO` used sparingly — only 2 found in `event_fusion.py`

**TypeScript:**
- JSDoc not used — no `/** */` blocks in frontend code
- Section dividers with em-dashes: `// ── Sub Components ──`
- Minimal inline comments; code is largely self-documenting via TypeScript types

## Function Design

**TypeScript:**
- Pages use a single `loadData()` async function called from `useEffect`
- Helper functions defined as standalone named functions at bottom of page files (not exported)
- Pure formatting helpers exported from `StockHelpers.tsx`: `formatPrice()`, `formatVolume()`, `formatMarketCap()`, `formatPercentage()`
- React components receive strongly-typed props interfaces

**Python:**
- Service classes use engine/singleton pattern: `scoring_engine = ScoringEngine()` at module bottom
- Private methods prefixed with `_`: `_resolve_weights()`, `_safe_float()`
- Async functions for all DB operations; sync functions for pure computation

## Module Design

**TypeScript Exports:**
- Pages: default export only (`export default function DashboardPage()`)
- Components: default export for main component + named exports for helpers (e.g., `StockHelpers.tsx`)
- API client: named interface exports + `export const api = {...}` + `export default api`
- No barrel `index.ts` files detected

**Python Exports:**
- Service singletons instantiated at module bottom and imported by name:
  ```python
  # at bottom of scoring.py
  scoring_engine = ScoringEngine()
  ```
- Pydantic models in `app/models/` imported directly by path
- `app/core/config.py` exports `settings = Settings()` singleton

## Client Directive Usage (Next.js)

- `'use client'` placed at top of every component/page that uses React hooks or browser APIs
- All page files and all components in `src/components/` use `'use client'`
- No Server Components with data fetching observed — all data loading is client-side via `useEffect`

---

*Convention analysis: 2026-04-16*
