# Phase 48: Veri Kalitesi Temeli - Context

**Gathered:** 2026-05-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 48 delivers a data quality scoring layer on top of yfinance BIST fundamental data. It adds `data_quality_score` (0-100) per stock via Alembic migration, implements USD→TRY sanity checks for PE/PB/EV-EBITDA fields, surfaces scores in both stock list and detail pages, and consolidates `safeLabel()` from inline copies (3 pages confirmed) into a single StockHelpers.tsx export.

This phase does NOT add tavan/taban, liquidity scoring, or regime detection — those are Phase 49+.

</domain>

<decisions>
## Implementation Decisions

### Data Quality Score UI
- Stock list: small inline colored badge next to score (red <50, yellow 50-75, green >75) — consistent with existing volatilite uyarı ikon pattern
- Threshold for "Düşük Veri Güveni" warning: score < 50
- Stock detail: append "Veri Güven Skoru" row to existing skor dökümü section
- Badge shows numeric score (e.g., "DK: 72") with tooltip explaining what it means

### USD Sanity Check Logic
- Fields checked: PE (trailingPE, forwardPE), PB (priceToBook), EV/EBITDA (enterpriseToEbitda)
- Suspicious PE threshold: PE < 0.5 or (PE > 0 and PE < 2) — BIST PE typically 5-25; USD-converted ~0.1-0.5
- Suspicious PB threshold: PB < 0.05 — BIST PB typically 0.5-5; USD-converted ~0.03-0.3
- When flagged: score still shown with "düşük güven" badge; UI warning is sufficient to satisfy VKL-01
- data_quality_score formula: starts at 100, subtracts 30 for each USD-suspicious field, subtracts 10 for each null fundamental field, minimum 0

### safeLabel Refactor
- Add as named export to StockHelpers.tsx alongside existing formatPrice, formatVolume exports
- 3 pages updated in same PR — atomic change (watchlist/backtest do NOT have inline safeLabel in codebase)
- Existing safeLabel callers updated to `import { safeLabel } from '@/components/StockHelpers'`

### Claude's Discretion
- Exact color palette for quality badges: use existing CSS vars (--accent-green, --accent-yellow, --accent-red)
- Alembic migration revision number: 008 (follows 007)
- data_quality_score computed in scoring.py at end of `calculate_overall_score()` or separate `calculate_data_quality()` method — Claude's choice based on existing structure

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `StockHelpers.tsx` — existing formatPrice, formatVolume, formatMarketCap, formatPercentage exports; safeLabel goes here
- `stocks.module.css` / `stock.module.css` — existing badge patterns for volatilite uyarı ikon
- `backend/app/services/scoring.py` — ScoringEngine singleton with `calculate_overall_score()` method
- `backend/app/models/stock.py` — Stock ORM model; `data_quality_score` column goes here
- `backend/alembic/versions/007_*.py` — last migration; 008 follows
- `backend/app/services/fundamental.py` — yfinance fundamental fetching; USD checks go here

### Established Patterns
- Alembic migration: inspector pattern (007) — `if "column" not in columns: op.add_column()`
- CSS badge pattern: inline badge with CSS module class, color via CSS var
- ScoringEngine: method-based singleton pattern; pure computation from Fundamental ORM row
- Frontend: `StockSummary` interface in `api.ts` — add `data_quality_score?: number | null`

### Integration Points
- `GET /stocks` endpoint → serialization dict → add `data_quality_score`
- `GET /stocks/{symbol}` endpoint → add `data_quality_score` to response
- `frontend/src/app/stocks/page.tsx` — stock list row → add quality badge
- `frontend/src/app/stocks/[symbol]/page.tsx` — skor dökümü section → add quality row
- `frontend/src/components/StockHelpers.tsx` — add safeLabel export
- 3 pages confirmed to have inline safeLabel: stocks/page.tsx, stocks/[symbol]/page.tsx, model-portfolio/page.tsx (watchlist/backtest do NOT have inline safeLabel — verified by grep)

</code_context>

<specifics>
## Specific Ideas

- Use "Düşük Veri Güveni" as the warning label (exact Turkish from requirements)
- Badge format: small pill badge, not full-width banner
- Tooltip on hover: "Bu hissenin temel verileri yfinance'te USD cinsinden görünüyor olabilir. Skorlar tahmini."
- Alembic migration should be idempotent (inspector pattern like 007)

</specifics>

<deferred>
## Deferred Ideas

- Per-field quality breakdown (which specific fields are suspicious) — Phase 49+ UI
- Alert/notification when quality drops for a watchlist stock — out of scope
- Historical quality score tracking — out of scope

</deferred>
