# Phase 49: Veri Zenginleştirme - Context

**Gathered:** 2026-05-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 49 delivers four data enrichment features on top of the Phase 48 data quality foundation:
1. **VKL-03** — Circuit breaker (tavan/taban) badge: frontend-only display rule; no DB column.
2. **VKL-04** — Amihud illiquidity scoring: DB columns + backend computation + frontend badge/warning.
3. **KAP-01** — KAP announcement type classification: new `kap_category` column on `news_items` + classification logic in `kap_parser.py`.
4. **KAP-02** — KAP category badges in stock detail page.

This phase does NOT address REJ (market regime), SEK (sector scoring), PORT, NLP, or BACK — those are Phase 50+.
</domain>

<decisions>
## Implementation Decisions

### VKL-03: Tavan/Taban Badge (Circuit Breaker)
- Frontend-only — no backend DB column needed.
- Tavan (upper circuit): `daily_change_pct >= 9.8` (BIST %10 limit hits at ~9.8-9.99%).
- Taban (lower circuit): `daily_change_pct <= -9.8`.
- Computed from `stock.daily_change_pct` already present in `StockSummary`.
- Badge placement:
  - Stock list (`stocks/page.tsx`): inline in the `daily_change_pct` cell, after the change value.
  - Stock detail (`stocks/[symbol]/page.tsx`): near the price hero (next to price display).
- Badge text: "TAVAN" (green background) or "TABAN" (red background).
- CSS classes in respective `.module.css` files using existing `--accent-green` / `--accent-red` CSS vars.

### VKL-04: Amihud Illiquidity Scoring
- Computation: 30-day rolling mean of `|return| / volume` per day from `PriceHistory` table.
  - Return = `(close - prev_close) / prev_close` for each consecutive day pair.
  - Amihud ratio per day = `abs(return) / volume` (skip if volume is 0 or null).
  - 30-day mean = average over last 30 valid rows.
- Thresholds:
  - `amihud_ratio < 0.001` → `liquidity_score = "yüksek"`
  - `0.001 <= amihud_ratio <= 0.01` → `liquidity_score = "orta"`
  - `amihud_ratio > 0.01` → `liquidity_score = "düşük"`
- DB columns: `stocks.liquidity_score VARCHAR(20) nullable`, `stocks.amihud_ratio FLOAT nullable` — added via Alembic migration 009.
- Implementation location: new method `calculate_amihud_liquidity(stock_id, db)` in `backend/app/services/scoring.py`; called from `update_all_scores()` after overall score is set.
- API: add `liquidity_score` and `amihud_ratio` to `/stocks` list and `/stocks/{symbol}` serialization dicts in `backend/app/api/stocks.py`.
- Frontend:
  - `StockSummary` in `api.ts` already has `liquidity_score?: string | null` and `liquidity_level?` — add `amihud_ratio?: number | null`.
  - Stock list: add liquidity badge in score column area (only show "düşük" as warning, others as informational).
  - Stock detail: show liquidity level row and show warning banner if "düşük".

### KAP-01: KAP Announcement Classification
- New DB column: `news_items.kap_category VARCHAR(50) nullable` — in migration 009.
- Column purpose: human-readable Turkish category name (NOT the same as existing `category` field which holds internal event_type codes like "dividend", "earnings").
- Classification mapping from existing `_classify_event` output to `kap_category`:
  ```
  "dividend"      → "Temettü"
  "bonus_issue"   → "Sermaye Artırımı"   (bedelsiz)
  "rights_issue"  → "Sermaye Artırımı"   (bedelli)
  "buyback"       → "Pay Geri Alımı"
  "earnings"      → "Finansal Sonuçlar"
  "investment"    → "Yatırım"
  "tender"        → "İhale"
  "contract"      → "Sözleşme"
  "credit_rating" → "Kredi Notu"
  "financing"     → "Finansman"
  "share_sale"    → "İçeriden Öğrenme"
  "merger"        → "Birleşme/Devralma"
  "governance"    → "Yönetim"
  "legal"         → "Hukuki"
  "restructuring" → "Yeniden Yapılanma"
  "other"         → "Diğer"
  ```
- Implementation: add `_event_type_to_kap_category(event_type: str) -> str` helper method in `KAPParser`; call it in `store_announcements()` when creating `NewsItem`, set `news_item.kap_category = self._event_type_to_kap_category(event_type)`.
- No keyword-based classification needed — reuse existing `_classify_event` output, just map to Türkçe display label.
- High-impact categories (for VKL-04 badge prominence): "Temettü", "Sermaye Artırımı", "İçeriden Öğrenme", "Hukuki".

### KAP-02: Category Badges in Stock Detail UI
- `StockNewsItem` interface in `api.ts`: add `kap_category?: string | null`.
- Backend `GET /stocks/{symbol}/news` (or equivalent news endpoint): add `kap_category` field to news item serialization.
- Stock detail `NewsRow` component: render `kap_category` badge before title.
- Badge styling: small pill badge with category name.
  - High-impact categories get `--accent-red` or highlighted background.
  - Other categories get neutral/muted style.
- Badge color rules: "Temettü" → green, "Sermaye Artırımı" → amber, "İçeriden Öğrenme" → red, "Hukuki" → red, everything else → muted/gray.

### Migration 009
- Single migration combining VKL-04 and KAP-01 columns.
- `revision = "009"`, `down_revision = "008"`.
- Idempotent inspector pattern (same as migrations 007, 008).
- Adds:
  - `stocks.liquidity_score VARCHAR(20) nullable`
  - `stocks.amihud_ratio FLOAT nullable`
  - `news_items.kap_category VARCHAR(50) nullable`

### Claude's Discretion
- Amihud ratio values for BIST stocks with low volume can be very large; cap the stored value at 1.0 for display sanity.
- If fewer than 5 price rows exist for a stock, skip Amihud computation and leave `liquidity_score = None`.
- The news endpoint for stock detail: check if it's `/stocks/{symbol}/news` or served via a different route — read `backend/app/api/stocks.py` at task time.
</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/alembic/versions/008_add_data_quality_score.py` — migration 008 is the direct predecessor; 009 follows with `down_revision = "008"`.
- `backend/app/services/scoring.py` — `ScoringEngine.update_all_scores()` is the integration point; `calculate_data_quality_score` pattern shows how to add a standalone function + call in update loop.
- `backend/app/services/kap_parser.py` — `KAPParser._classify_event()` returns event_type strings; `store_announcements()` creates `NewsItem` objects — add `kap_category` assignment here.
- `backend/app/api/stocks.py` — two serialization dicts: list (around line 161) and detail (around line 291); same pattern as Phase 48.
- `frontend/src/lib/api.ts` — `StockNewsItem` interface at line 581; `StockSummary` at line 46 (already has `liquidity_score?: string | null`).
- `frontend/src/app/stocks/[symbol]/page.tsx` — `NewsRow` component at line 89; news section at line 1035.

### Established Patterns
- Alembic migration: idempotent inspector pattern — inspect both "stocks" and "news_items" tables separately.
- CSS badge pattern: inline pill with CSS module class, color via CSS var (`--accent-green`, `--accent-amber`, `--accent-red`, `--text-muted`).
- ScoringEngine: method-based singleton pattern; async methods for DB operations.
- `PriceHistory` table: has `close`, `volume`, `date` columns — all needed for Amihud.

### Integration Points
- `GET /stocks` → serialization dict → add `liquidity_score`, `amihud_ratio`
- `GET /stocks/{symbol}` → add `liquidity_score`, `amihud_ratio`
- News endpoint → add `kap_category` to news item serialization
- `frontend/src/app/stocks/page.tsx` — daily change cell and score area → add tavan/taban badge + liquidity badge
- `frontend/src/app/stocks/[symbol]/page.tsx` — price hero → tavan/taban badge; score section → liquidity row; NewsRow → kap_category badge
- `frontend/src/lib/api.ts` — add `amihud_ratio?: number | null` to StockSummary; add `kap_category?: string | null` to StockNewsItem

</code_context>

<specifics>
## Specific Implementation Notes

- Tavan/taban badge: pure CSS class, no JS state — compute inline in JSX: `{(stock.daily_change_pct ?? 0) >= 9.8 && <span className={styles.tavanBadge}>TAVAN</span>}`.
- Amihud computation order in SQL: fetch last 31 price rows ordered by date desc (31 to compute 30 returns), then compute in Python.
- `kap_category` is NOT the same as the existing `category` field (which is the internal event_type code). They live in separate columns.
- Stock detail page uses `StockDetail` which extends `StockSummary` — liquidity fields flow through automatically once added to StockSummary.
- Stock detail news fetch: trace the `api.getStockNews(symbol)` call in page.tsx to find the endpoint and its serialization in stocks.py.
</specifics>

<deferred>
## Deferred Ideas

- Amihud-based slippage in backtest — that's BACK-01 (Phase 54).
- Illiquidity alert/notification — out of scope.
- KAP category filter in news feed (Intelligence page) — Phase 50+.
- Per-announcement Türkçe NLP sentiment — NLP-01 (Phase 53).
</deferred>
