# Phase 28: Veri Altyapısı - Research

**Researched:** 2026-05-04
**Domain:** BIST100 data pipeline — prices, fundamentals, technicals, scoring; forex and gold data
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DASH-01 | API, BIST100 endeksinin günlük değişimini ve hacmini döndürür | `XU100.IS` via yfinance; BloombergHT fallback already implemented in `macro.py`; extend `CommodityPrice` read |
| DASH-02 | API, 5-10 döviz çiftini döndürür (USD/TRY, EUR/TRY, GBP/TRY vb.) | yfinance `*TRY=X` symbols; already in `CURRENCY_PAIRS` config; add JPY, CHF, RUB; new `/market/forex` endpoint |
| DASH-03 | API, altının beş formunu (gram, ons, çeyrek, yarım, tam) döndürür | yfinance `GC=F` (USD/oz) + `USDTRY=X` → compute TRY/gram then multiply by coin weights; new `/market/gold` endpoint |
| DISC-01 | Kullanıcı BIST100 hisselerini temel + teknik skora göre filtreler ve sıralar | `Stock.fundamental_score` + `Stock.technical_score` already on model; `/stocks` endpoint already supports `sort_by`, `bist100` filter; verify scores actually populated |
| DISC-02 | Kullanıcı "bugün ilginç hisseler" listesini görür (yüksek skor = öne çıkar) | `Stock.overall_score` already computed; new `/market/opportunities` endpoint returning top N BIST100 by overall_score |
</phase_requirements>

---

## Summary

Phase 28 builds the data plumbing that every downstream phase depends on. The existing codebase is substantially more complete than a greenfield: BIST100 price collection, technical indicator computation, fundamental scoring, and a combined `overall_score` are all implemented and working. The gaps are specific and bounded: (1) the `/macro/indicators` endpoint only exposes USD/TRY and one gold form — it must be extended to serve all 5 gold forms and 5-10 forex pairs via dedicated endpoints; (2) the BIST100 index summary (DASH-01) already exists in `CommodityPrice` as `XU100.IS` but has no dedicated endpoint with volume and daily change; (3) no dedicated "opportunities" endpoint (DISC-02) exists — the `/rankings` endpoint is close but not scoped to BIST100 + overall_score only.

The scoring engine already uses `fundamental_score * 0.45 + technical_score * 0.40 + sentiment_score * 0.15` (with normalization when scores are missing). The fundamental engine fetches F/K (PE), PD/DD (PB), ROE, net margin, D/E from yfinance. The technical engine computes RSI-14, MACD, SMA20/50/200, EMA12/26/50/200, Bollinger Bands, ATR-14, ADX, OBV, and writes them to `PriceHistory`. Both engines already update `Stock.fundamental_score` and `Stock.technical_score` respectively, which `scoring_engine.update_all_scores()` then combines into `Stock.overall_score`.

**Primary recommendation:** Reuse all existing engines and models. Add three new read-only endpoints (`/market/bist100`, `/market/forex`, `/market/gold`) and ensure the data pipeline scheduler is locked to BIST100-only. No schema migrations are needed unless fundamental metric columns are missing from `Stock` for fast list queries.

---

## Standard Stack

### Core (already in use — no additions needed)
| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| yfinance | 0.2.54 | OHLCV history, fundamentals, forex pairs, gold futures | Primary price source; `GC=F` for gold, `*TRY=X` for forex, `XU100.IS` for BIST100 index |
| ta | 0.11.0 | Technical indicators (RSI, MACD, Bollinger, ATR, EMA) | Already used in `technical.py`; no changes needed |
| pandas | 2.2.3 | DataFrame manipulation for indicator calculation | Already used |
| SQLAlchemy 2.0 (asyncio) | 2.0.40 | Async ORM; `Stock`, `PriceHistory`, `CommodityPrice`, `Fundamental` | Already used |
| FastAPI | 0.115.12 | REST endpoints | Already used |
| APScheduler | 3.11.0 | Background job orchestration | Already drives `daily_update()` |
| diskcache | (existing) | yfinance result-level cache (1GB cap) | Already used in `data_collector.py` |
| requests | 2.32.3 | Sync HTTP for BloombergHT/Foreks live quotes | Already used |

### Gold Calculation — No External Library Needed
Turkish gold coin weights are fixed physical constants:

| Form | Weight (grams, 22-karat) | Multiplier vs gram |
|------|--------------------------|-------------------|
| Gram | 1.0 | 1.0 |
| Ons (troy oz) | 31.1035 | 31.1035 |
| Çeyrek | ~1.754 | 1.754 |
| Yarım | ~3.508 | 3.508 |
| Tam | ~7.016 | 7.016 |

Conversion formula: `gold_try_per_gram = GC_F_close_usd * usdtry / 31.1035`
Then multiply by coin weight to get each form's TRY price.

**No new pip packages needed.** Everything required is already installed.

---

## Architecture Patterns

### Existing Structure (What Can Be Reused)

```
backend/app/
├── services/
│   ├── data_collector.py     ← REUSE: DataCollector, get_yahoo_chart_history
│   ├── technical.py          ← REUSE: TechnicalAnalysisEngine (analyze_all, analyze_stock)
│   ├── fundamental.py        ← REUSE: FundamentalAnalysisEngine
│   └── scoring.py            ← REUSE: ScoringEngine (update_all_scores, get_rankings)
├── models/
│   ├── stock.py              ← REUSE: Stock model (has fundamental_score, technical_score, overall_score)
│   ├── price.py              ← REUSE: PriceHistory, CommodityPrice (stores gold, forex, BIST100 history)
│   └── fundamental.py        ← REUSE: Fundamental model (pe_ratio, pb_ratio, net_income etc.)
├── api/
│   ├── stocks.py             ← REUSE: /stocks (supports bist100 filter + sort_by overall_score)
│   └── macro.py              ← EXTEND: add /market/* endpoints here or new router
└── core/
    └── config.py             ← EXTEND: add missing forex pairs (JPY, CHF, RUB, SAR, AED)
```

### New Endpoints Pattern (follow existing stocks.py style)

Three new GET endpoints, all read-only, no auth required, with simple in-memory TTL cache (60s like `_indicators_cache` in `macro.py`):

```
GET /api/v1/market/bist100       ← BIST100 index: value, daily_change_pct, volume, as_of
GET /api/v1/market/forex         ← 5-10 forex pairs with name, symbol, rate, change_pct, as_of  
GET /api/v1/market/gold          ← 5 gold forms (gram, ons, çeyrek, yarım, tam) with TRY price, as_of
GET /api/v1/market/opportunities ← Top 20 BIST100 stocks by overall_score (DISC-02)
```

### BIST100 Index Data Pattern
Data source priority (already established in `macro.py`):
1. `CommodityPrice` DB table (symbol=`XU100.IS`) — freshest scheduled data
2. Yahoo Finance API fallback if DB data is stale (>1 day old)
3. BloombergHT HTML scrape as live fallback (`_fetch_bloomberght_bist100()` already exists)

Volume and daily change: yfinance `XU100.IS` history provides volume; daily change = `(close[-1] - close[-2]) / close[-2] * 100`.

### Forex Data Pattern
Config already has: `usd_try`, `eur_try`, `gbp_try`, `cny_try`, `dxy`. Need to add: `jpy_try` (JPYTRY=X), `chf_try` (CHFTRY=X). All stored in `CommodityPrice` with `category='currency'`.

Read from `CommodityPrice` where `category='currency'`, take latest date per symbol. Fall back to yfinance live fetch if stale.

### Gold Data Pattern (DASH-03 — most complex)
yfinance already collects `GC=F` (gold futures USD/oz) and `USDTRY=X` in `CommodityPrice`. The conversion already exists in `macro.py` (`gold_try = gold_usd * usdtry / 31.1035`).

New endpoint extends this by applying coin weight multipliers:
```python
GOLD_FORMS = {
    "gram": 1.0,
    "ons": 31.1035,
    "ceyrek": 1.754,
    "yarim": 3.508,
    "tam": 7.016,
}
```

### Scoring Engine — No Changes Needed
Weights are already set: `WEIGHT_FUNDAMENTAL=0.45`, `WEIGHT_TECHNICAL=0.40`, `WEIGHT_NEWS=0.15`. The `ScoringEngine._resolve_weights()` normalizes when a component is missing. `Stock.overall_score` is updated by `scoring_engine.update_all_scores()` which runs in `daily_update()`.

For DISC-01 and DISC-02, use existing `/stocks` endpoint with `bist100=true&sort_by=overall_score` for filtering. For a dedicated opportunities endpoint, query `Stock` WHERE `is_bist100=true AND overall_score IS NOT NULL ORDER BY overall_score DESC LIMIT 20`.

### Scheduler — BIST100 Scope Lock
`DataCollector.__init__` already reads from `settings.BIST100_UNIVERSE` (not BIST_FULL_UNIVERSE). Verify `initialize_stocks()` only creates stocks with `is_bist100=True`. The `collect_live_bist_quotes()` uses `self.symbols` which comes from `BIST100_UNIVERSE`. No changes needed to scope.

### Anti-Patterns to Avoid
- **Don't compute gold forms in the frontend.** Keep all coin weight math in the backend API endpoint.
- **Don't add a new DB table for gold forms.** Derive them at query time from `GC=F` + `USDTRY=X` — these are calculated values, not stored facts.
- **Don't run `full_initial_load()` on every startup.** It's already guarded by `RUN_FULL_INITIAL_LOAD_ON_STARTUP=False`.
- **Don't add N+1 queries in the opportunities endpoint.** Use a single `SELECT` with `ORDER BY overall_score DESC` — no join to `Fundamental` needed since scores are already denormalized on `Stock`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| RSI, MACD, Bollinger, ATR | Custom formula | `ta` library (already used) | Edge cases in period warmup, NaN handling |
| BIST100 live prices | Direct exchange connection | BloombergHT/Foreks JSON API (already implemented) | Rate limits, auth, format parsing solved |
| Gold USD→TRY conversion | Custom FX API | yfinance `GC=F` + `USDTRY=X` math (already in macro.py) | Both data points already scheduled and cached |
| Fundamental score calculation | Custom scoring engine | Existing `FundamentalAnalysisEngine._calculate_score()` | Already handles PE, PB, ROE, net margin, D/E |
| Combined opportunity score | Custom weighted average | Existing `ScoringEngine.calculate_overall_score()` | Normalization for missing components already solved |
| Historical price backfill | Custom scraper | yfinance `get_yahoo_chart_history(period="5y")` | Already implemented with retry and diskcache |

---

## Common Pitfalls

### Pitfall 1: yfinance BIST100 Index Volume is Often Zero
**What goes wrong:** `XU100.IS` history often returns `Volume=0` or NaN for the index (indices don't have exchange-reported volume the same way stocks do).
**Why it happens:** Borsa Istanbul reports index values, not trade volume directly to Yahoo.
**How to avoid:** Use volume from `XU100.IS` if non-zero; otherwise report `null` in the API response. Do not fabricate a fallback volume value. BIST100 daily turnover (hacim) is a different metric — it's aggregate stock turnover, not index "volume".
**Warning signs:** All `XU100.IS` history rows show `Volume=0`.

### Pitfall 2: Gold Coin Weights Are Nominal, Not Exact
**What goes wrong:** The user sees "Çeyrek: 1.754g" but their bank uses slightly different weight (1.7540–1.7560g varies by mint year).
**Why it happens:** Standard çeyrek is 1.754g (22-karat), but Cumhuriyet coin variations exist.
**How to avoid:** Use 1.754g for çeyrek, 3.508g for yarım, 7.016g for tam as standard approximations. This matches what Bigpara and Turkish banks use for indicative pricing. Document in code that these are approximate.

### Pitfall 3: `fundamental_score` NULL for Many Stocks
**What goes wrong:** yfinance fundamental data for many BIST100 stocks is sparse or missing — especially smaller-cap stocks. `fundamental_score` on `Stock` is NULL; `overall_score` calculation degrades gracefully (normalizes weights) but the score reflects only technical + sentiment.
**Why it happens:** yfinance `ticker.info` has incomplete Turkish stock coverage; many fields return `None`.
**How to avoid:** The existing `ScoringEngine._resolve_weights()` already handles this correctly. Accept that some stocks will have fundamental_score=NULL. DISC-01 filtering by fundamental score will return fewer stocks — document this as expected behavior, not a bug.

### Pitfall 4: Race Condition Between Daily Update and API Read
**What goes wrong:** `daily_update()` calls `technical_engine.analyze_all()` which opens its own `AsyncSessionLocal()` and commits per stock, while simultaneously an API request reads `Stock.overall_score`. Partial state is visible.
**Why it happens:** No transaction isolation at the batch level — each stock is committed separately.
**How to avoid:** This is an existing behavior, not introduced by Phase 28. Scores are eventually consistent (max staleness = one scheduler cycle, ~5min for live prices). Accept this for a personal tool — no locking needed.

### Pitfall 5: BloombergHT Scraping is Fragile
**What goes wrong:** The HTML scraping in `_fetch_bloomberght_bist100()` relies on a regex pattern against page text. HTML layout changes break it silently (returns `None, None` without error).
**Why it happens:** No contract with BloombergHT — scraping, not a public API.
**How to avoid:** Keep BloombergHT as a tertiary fallback only. Primary source is `CommodityPrice` DB; secondary is Yahoo Finance API. If BloombergHT returns None, log a WARNING and use the Yahoo value. Do not block the endpoint on BloombergHT.

### Pitfall 6: Currency Pairs Need `change_pct` Computed
**What goes wrong:** `CommodityPrice` has a `change_pct` column but `data_collector.py`'s `collect_market_data()` does not populate it — only OHLCV is written.
**Why it happens:** `change_pct` is optional and was not computed at ingest time.
**How to avoid:** In the new `/market/forex` endpoint, compute `change_pct = (today.close - yesterday.close) / yesterday.close * 100` by fetching the two most recent rows per symbol. Do not rely on `CommodityPrice.change_pct` field being populated.

---

## Code Examples

### BIST100 Index Endpoint Pattern
```python
# Source: existing macro.py pattern adapted for new endpoint
@router.get("/market/bist100")
async def get_bist100_summary(db: AsyncSession = Depends(get_db)):
    # Fetch 2 most recent rows for daily change calculation
    rows = await db.execute(
        select(CommodityPrice)
        .where(CommodityPrice.symbol == "XU100.IS")
        .order_by(CommodityPrice.date.desc())
        .limit(2)
    )
    prices = rows.scalars().all()
    if not prices:
        raise HTTPException(status_code=503, detail="BIST100 verisi yok")
    today = prices[0]
    yesterday = prices[1] if len(prices) > 1 else None
    change_pct = None
    if yesterday and yesterday.close:
        change_pct = (today.close - yesterday.close) / yesterday.close * 100
    return {
        "value": round(today.close, 2),
        "daily_change_pct": round(change_pct, 2) if change_pct else None,
        "volume": today.volume if today.volume else None,
        "as_of": today.date.isoformat(),
    }
```

### Gold Forms Endpoint Pattern
```python
# Source: existing macro.py gold_try conversion logic, extended
GOLD_COIN_WEIGHTS = {
    "gram": 1.0,
    "ons": 31.1035,
    "ceyrek": 1.754,   # çeyrek altın, 22-karat
    "yarim": 3.508,    # yarım altın, 22-karat
    "tam": 7.016,      # tam altın, 22-karat
}

@router.get("/market/gold")
async def get_gold_prices(db: AsyncSession = Depends(get_db)):
    gold_usd_row = await _latest_market_reading(db, "GC=F")  # existing helper
    usdtry_row = await _latest_market_reading(db, "USDTRY=X")  # existing helper
    if not gold_usd_row[0] or not usdtry_row[0]:
        raise HTTPException(status_code=503, detail="Altın verisi yok")
    
    gold_usd, gold_as_of = gold_usd_row
    usdtry, _ = usdtry_row
    gram_try = gold_usd * usdtry / 31.1035

    return {
        "forms": {
            form: round(gram_try * weight, 2)
            for form, weight in GOLD_COIN_WEIGHTS.items()
        },
        "gold_usd_per_oz": round(gold_usd, 2),
        "usdtry": round(usdtry, 4),
        "as_of": gold_as_of,
    }
```

### Opportunities Endpoint (DISC-02)
```python
# Source: existing scoring.py get_rankings() pattern
@router.get("/market/opportunities")
async def get_opportunities(
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Top BIST100 stocks by combined opportunity score."""
    result = await db.execute(
        select(Stock)
        .where(Stock.is_bist100 == True, Stock.is_active == True, Stock.overall_score.isnot(None))
        .order_by(Stock.overall_score.desc())
        .limit(limit)
    )
    stocks = result.scalars().all()
    return {
        "stocks": [
            {
                "symbol": s.symbol,
                "name": s.name,
                "sector": s.sector,
                "current_price": s.current_price,
                "daily_change_pct": s.daily_change_pct,
                "overall_score": s.overall_score,
                "fundamental_score": s.fundamental_score,
                "technical_score": s.technical_score,
                "recommendation": s.recommendation,
            }
            for s in stocks
        ],
        "count": len(stocks),
        "as_of": datetime.now(timezone.utc).isoformat(),
    }
```

### Forex Endpoint Pattern
```python
# Source: existing CommodityPrice pattern + change_pct computation
FOREX_PAIRS = {
    "USDTRY=X": "USD/TRY",
    "EURTRY=X": "EUR/TRY",
    "GBPTRY=X": "GBP/TRY",
    "CNYTRY=X": "CNY/TRY",
    "JPYTRY=X": "JPY/TRY",
    "CHFTRY=X": "CHF/TRY",
}

@router.get("/market/forex")
async def get_forex_rates(db: AsyncSession = Depends(get_db)):
    pairs = []
    for symbol, name in FOREX_PAIRS.items():
        rows = await db.execute(
            select(CommodityPrice)
            .where(CommodityPrice.symbol == symbol)
            .order_by(CommodityPrice.date.desc())
            .limit(2)
        )
        data = rows.scalars().all()
        if not data:
            continue
        today = data[0]
        yesterday = data[1] if len(data) > 1 else None
        change_pct = None
        if yesterday and yesterday.close:
            change_pct = (today.close - yesterday.close) / yesterday.close * 100
        pairs.append({
            "symbol": symbol,
            "name": name,
            "rate": round(today.close, 4),
            "daily_change_pct": round(change_pct, 2) if change_pct else None,
            "as_of": today.date.isoformat(),
        })
    return {"pairs": pairs, "as_of": datetime.now(timezone.utc).isoformat()}
```

---

## What Needs to Change vs What Can Be Reused

### REUSE AS-IS (no code changes)
- `DataCollector` — already BIST100 scoped
- `TechnicalAnalysisEngine` — calculates RSI, MACD, MA; writes to `PriceHistory` and `Stock.technical_score`
- `FundamentalAnalysisEngine` — fetches PE, PB, ROE, net margin, D/E from yfinance; writes `Fundamental` records + `Stock.fundamental_score`
- `ScoringEngine` — combines fundamental + technical + sentiment into `Stock.overall_score`
- `Stock` model — already has all needed score columns
- `PriceHistory` model — already has RSI, MACD, SMA, EMA, ATR, OBV columns
- `Fundamental` model — already has PE, PB, net_income, revenue_growth_yoy, earnings_growth_yoy
- `/stocks` endpoint — supports `bist100=true` + `sort_by=overall_score` (DISC-01 is already there)
- `daily_update()` scheduler job — already calls price collection + technical analysis + scoring

### EXTEND (minimal changes)
- `config.py` CURRENCY_PAIRS — add JPY, CHF (currently missing; DX-Y.NYB/DXY is not a TRY pair)
- `macro.py` — add three new endpoints: `/market/bist100`, `/market/forex`, `/market/gold`; OR add a new `market.py` router
- `main.py` router mounting — if new `market.py` router added, mount it

### NEW (create from scratch)
- `GET /api/v1/market/bist100` — BIST100 index summary (value, daily_change_pct, volume)
- `GET /api/v1/market/forex` — 5-10 forex pairs with rates and daily change
- `GET /api/v1/market/gold` — 5 gold forms computed from GC=F + USDTRY=X
- `GET /api/v1/market/opportunities` — top 20 BIST100 by overall_score (DISC-02)

### VERIFY (may already work, needs confirmation)
- Are `Stock.overall_score`, `Stock.fundamental_score`, `Stock.technical_score` populated for BIST100 stocks in production? Check via `/stocks?bist100=true&sort_by=overall_score&limit=5`.
- Does `collect_market_data()` scheduler correctly populate `CommodityPrice` for `USDTRY=X`, `EURTRY=X`, `GBPTRY=X`, `XU100.IS`?
- Is `JPYTRY=X` already in CURRENCY_PAIRS? (It is not — `cny_try: CNYTRY=X` is there, but JPY is missing.)

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| BIST ALL (399 stocks) | BIST100 only (v4.0) | DataCollector already uses `BIST100_UNIVERSE`; confirmed in code |
| Gold: only gram via macro.py | Gold: all 5 forms via new endpoint | New computation layer on top of existing GC=F + USDTRY=X |
| Forex: 5 pairs in config | Forex: need JPY/TRY + CHF/TRY added | Minor config addition |
| `/macro/indicators`: combined endpoint | Separate `/market/*` endpoints per concern | Cleaner API contract for Phase 29 Dashboard |

---

## Open Questions

1. **Is the existing BloombergHT stock slug API stable?**
   - What we know: `_fetch_bloomberght_stock_slugs()` caches slugs 1h from `ekonomi/borsa/bist/tum/hisseler`. Has worked in v3.1.
   - What's unclear: API is undocumented; can break without notice.
   - Recommendation: Keep as primary live price source but implement yfinance as automatic fallback — already done in `collect_live_bist_quotes()`.

2. **Should the `/market/gold` endpoint fall back to yfinance live fetch if DB data is stale?**
   - What we know: `macro.py` already does this pattern with `_market_reading_is_stale()`.
   - Recommendation: Yes, reuse the same stale-check + live-fetch pattern from `macro.py`. TTL: 60s in-memory cache.

3. **Do we need `net_kar` (net income) and `bilanço büyümesi` (balance sheet growth) specifically as API fields for DISC-01?**
   - What we know: `Fundamental` model has `net_income`, `revenue_growth_yoy`, `earnings_growth_yoy`. These are populated by `FundamentalAnalysisEngine` from yfinance when available.
   - What's unclear: yfinance coverage for BIST100 fundamentals is inconsistent; STCK-02 (Phase 30) is where these fields are displayed with tooltips.
   - Recommendation: Phase 28 ensures these fields are stored and populated in `Fundamental`. Phase 30 consumes them for display. No additional API surface needed in Phase 28 beyond what `/stocks/{symbol}/fundamentals` already returns.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (inferred from CI `backend/requirements.txt`) |
| Config file | `backend/pytest.ini` or none — check Wave 0 |
| Quick run command | `cd backend && python -m pytest tests/ -x -q` |
| Full suite command | `cd backend && python -m pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DASH-01 | `/market/bist100` returns value + daily_change_pct | unit (FastAPI TestClient) | `pytest tests/test_market_endpoints.py::test_bist100_endpoint -x` | ❌ Wave 0 |
| DASH-02 | `/market/forex` returns ≥5 pairs with rates | unit (FastAPI TestClient) | `pytest tests/test_market_endpoints.py::test_forex_endpoint -x` | ❌ Wave 0 |
| DASH-03 | `/market/gold` returns all 5 forms with TRY prices | unit (FastAPI TestClient) | `pytest tests/test_market_endpoints.py::test_gold_endpoint -x` | ❌ Wave 0 |
| DISC-01 | `/stocks?bist100=true&sort_by=overall_score` returns sorted BIST100 list | integration | `pytest tests/test_stocks_endpoint.py::test_bist100_filter -x` | ❌ Wave 0 |
| DISC-02 | `/market/opportunities` returns top N by overall_score | unit | `pytest tests/test_market_endpoints.py::test_opportunities_endpoint -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd backend && python -m pytest tests/test_market_endpoints.py -x -q`
- **Per wave merge:** `cd backend && python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_market_endpoints.py` — covers DASH-01, DASH-02, DASH-03, DISC-02 with mock DB fixtures
- [ ] `backend/tests/test_stocks_endpoint.py` — covers DISC-01 bist100 filter + overall_score sort
- [ ] `backend/tests/conftest.py` — shared async DB session fixture if not present
- [ ] Framework install check: `cd backend && python -m pytest --version` — verify pytest available

---

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `backend/app/services/data_collector.py` — confirmed yfinance symbols, BloombergHT integration, `CommodityPrice` write pattern
- Codebase analysis: `backend/app/services/technical.py` — confirmed RSI, MACD, EMA, ATR calculation via `ta` library
- Codebase analysis: `backend/app/services/scoring.py` — confirmed `WEIGHT_FUNDAMENTAL=0.45`, `WEIGHT_TECHNICAL=0.40`, `WEIGHT_NEWS=0.15`
- Codebase analysis: `backend/app/api/macro.py` — confirmed existing gold TRY conversion formula and BIST100 fetch pattern
- Codebase analysis: `backend/app/models/` — confirmed `Stock`, `PriceHistory`, `Fundamental`, `CommodityPrice` schemas
- Codebase analysis: `backend/app/core/config.py` — confirmed `CURRENCY_PAIRS` and `INDEX_SYMBOLS` definitions

### Secondary (MEDIUM confidence)
- Yahoo Finance (confirmed live): `XU100.IS` returns index value and history; BIST100 at 14,369 as of 2026-05-04
- [Yahoo Finance XU100.IS](https://finance.yahoo.com/quote/XU100.IS/) — BIST100 index data available
- [MetalTakip](https://www.metaltakip.com/en/prices) — confirms Turkish gold coin weights (çeyrek ≈1.754g, yarım ≈3.508g, tam ≈7.016g)

### Tertiary (LOW confidence)
- yfinance `JPYTRY=X`, `CHFTRY=X` availability — not verified via live call; assumed by pattern (existing `CNYTRY=X` works)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in use and confirmed in codebase
- Architecture: HIGH — direct codebase reading; no assumptions
- Gold coin weights: MEDIUM — confirmed by MetalTakip; nominal values may vary ±0.02g
- New forex pairs availability: LOW — `JPYTRY=X`, `CHFTRY=X` assumed available from yfinance by pattern; should be validated in Wave 0

**Research date:** 2026-05-04
**Valid until:** 2026-06-04 (stable domain; yfinance API changes would invalidate earlier)
