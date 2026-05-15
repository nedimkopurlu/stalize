---
phase: 49-veri-zenginlestirme
plan: 01
subsystem: backend
tags: [liquidity, amihud, kap, scoring, migration, orm, api]
dependency_graph:
  requires: [48-01]
  provides: [VKL-04-backend, KAP-01-backend]
  affects: [49-02, scoring_engine, kap_parser, stocks_api]
tech_stack:
  added: []
  patterns:
    - Idempotent Alembic migration (inspector pattern, migration 008)
    - TDD RED/GREEN for pure-function threshold logic
    - Async DB query in scoring pipeline (calculate_amihud_liquidity)
    - Turkish keyword mapping in KAP classifier
key_files:
  created:
    - backend/alembic/versions/009_add_liquidity_and_kap_category.py
    - backend/tests/test_amihud_and_kap_category.py
  modified:
    - backend/app/models/stock.py
    - backend/app/models/news.py
    - backend/app/services/scoring.py
    - backend/app/services/kap_parser.py
    - backend/app/api/stocks.py
decisions:
  - Renamed existing traded-value liquidity score to traded_liquidity_score in list endpoint to avoid key collision with Amihud-based liquidity_score ORM column
  - Amihud ratio capped at 1.0 to prevent extreme outliers distorting score label
  - Fewer than 5 price rows returns (None, None) rather than defaulting to "düşük" — explicit null is more honest than a guess
metrics:
  duration: ~18 minutes
  completed: 2026-05-15
  tasks: 3
  files: 5 modified, 2 created
---

# Phase 49 Plan 01: Veri Zenginleştirme — Amihud Likidite Skoru ve KAP Kategorisi Summary

**One-liner:** Amihud 30-day illiquidity ratio stored as `liquidity_score` VARCHAR and `amihud_ratio` FLOAT on stocks table; KAP announcements categorized to 16 Turkish display labels on news_items.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Alembic migration 009 + ORM model updates | ce4807f | 009_add_liquidity_and_kap_category.py, stock.py, news.py |
| 2 | Amihud computation + KAP category mapping (TDD) | c5f4594, d78b315 | scoring.py, kap_parser.py, test_amihud_and_kap_category.py |
| 3 | Expose new fields in API endpoints | fb4ce0b | stocks.py |

## What Was Built

### Migration 009 (idempotent)

File: `backend/alembic/versions/009_add_liquidity_and_kap_category.py`

- `revision = "009"`, `down_revision = "008"`
- Adds `liquidity_score VARCHAR(20) nullable` and `amihud_ratio FLOAT nullable` to `stocks` table
- Adds `kap_category VARCHAR(50) nullable` to `news_items` table
- Uses inspector pattern (like 008) — safe to run multiple times

### ORM Models

- `Stock.liquidity_score = Column(String(20), nullable=True)` — "yüksek" / "orta" / "düşük"
- `Stock.amihud_ratio = Column(Float, nullable=True)`
- `NewsItem.kap_category = Column(String(50), nullable=True)` — Turkish display label

### Amihud Computation (`scoring.py`)

Function signature:
```python
async def calculate_amihud_liquidity(stock_id: int, db) -> tuple:
```

Logic:
- Fetches last 31 `PriceHistory` rows ordered by date desc
- Requires at least 5 rows (otherwise returns `(None, None)`)
- Computes `mean(|return| / volume)` skipping rows with `volume == 0`
- Caps ratio at 1.0
- Thresholds: `< 0.001` → "yüksek", `0.001-0.01` → "orta", `> 0.01` → "düşük"

Integration in `update_all_scores()`:
```python
amihud_ratio, liquidity_score = await calculate_amihud_liquidity(stock.id, db)
stock.amihud_ratio = amihud_ratio
stock.liquidity_score = liquidity_score
```

### KAP Category Mapping (`kap_parser.py`)

Method: `KAPParser._event_type_to_kap_category(event_type: str) -> str`

Mapping covers all 16 event types from `_classify_event()`:
- dividend → "Temettü"
- earnings → "Finansal Sonuçlar"
- rights_issue / bonus_issue → "Sermaye Artırımı"
- share_sale → "İçeriden Öğrenme"
- buyback → "Pay Geri Alımı"
- merger → "Birleşme/Devralma"
- legal → "Hukuki"
- other / unknown → "Diğer" (fallback)

Called in `store_announcements()` as `kap_category=self._event_type_to_kap_category(event_type)` for each new `NewsItem`.

### API Endpoints (`stocks.py`)

- `GET /stocks` — adds `"liquidity_score": s.liquidity_score` and `"amihud_ratio": s.amihud_ratio`; existing traded-value score renamed to `"traded_liquidity_score"`
- `GET /stocks/{symbol}` — adds `"liquidity_score": stock.liquidity_score` and `"amihud_ratio": stock.amihud_ratio`
- `GET /stocks/{symbol}/news` — adds `"kap_category": item.kap_category` to each news item dict

## Test Results

```
13 passed, 2 warnings in 0.29s
```

Tests in `backend/tests/test_amihud_and_kap_category.py`:
- Tests 1-3: Amihud edge cases (normal tuple output, all-zero volume, < 5 rows)
- Tests 4-6: Amihud threshold classifier (yüksek/orta/düşük)
- Tests 7-13: KAP `_event_type_to_kap_category` all 7 event_type → Turkish label mappings incl. fallback

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - API Key Collision] Renamed traded-value liquidity score key in list endpoint**
- **Found during:** Task 3
- **Issue:** `GET /stocks` list response already had `"liquidity_score"` key mapped to `_list_liquidity()["score"]` (a traded-value computed float). Adding `"liquidity_score": s.liquidity_score` (ORM Amihud column) would silently overwrite it.
- **Fix:** Renamed the traded-value entry to `"traded_liquidity_score"` and added the Amihud ORM column as `"liquidity_score"` per plan spec.
- **Files modified:** `backend/app/api/stocks.py`
- **Commit:** fb4ce0b

## Known Stubs

None — all fields are real computed values or explicit `None` (when insufficient data).

## Self-Check: PASSED

- `backend/alembic/versions/009_add_liquidity_and_kap_category.py` — FOUND
- `backend/tests/test_amihud_and_kap_category.py` — FOUND
- Commits ce4807f, c5f4594, d78b315, fb4ce0b — all present in git log
- `grep -c '"liquidity_score":' backend/app/api/stocks.py` → 2
- `grep -c '"amihud_ratio":' backend/app/api/stocks.py` → 2
- `grep -c '"kap_category":' backend/app/api/stocks.py` → 1
- 13 tests pass
