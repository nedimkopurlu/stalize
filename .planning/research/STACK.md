# Technology Stack

**Project:** Stalize — BIST 100 AI Investment Advisor (v7.0 additions)
**Researched:** 2026-05-14
**Confidence:** HIGH for most; noted where MEDIUM or LOW

---

## Context

This is a **brownfield milestone research** — existing stack is locked. Python is pinned at **3.9** (CI hard constraint). The v6.0 STACK.md decisions (instructor, requests-cache, diskcache, Vercel AI SDK, XGBoost native format) remain valid and are NOT re-researched here.

**New capabilities needing library decisions for v7.0:**
1. Turkish NLP sentiment (replace vaderSentiment)
2. Market Regime Engine (bull/bear/sideways/volatile detection)
3. Sector-specific fundamental metrics (Banks, GYO, Holdings)
4. Portfolio analytics (beta + correlation matrix)
5. Backtesting with slippage + commission
6. Tavan/taban (circuit breaker) detection
7. Liquidity scoring

**Deployment constraint:** Railway free tier — ~512MB usable RAM per service (trial tier gives 1GB but free $5 credit tier is more constrained). All new library decisions must account for a **target of <200MB net RAM increase** across all v7.0 features combined.

---

## Existing Stack — Keep As-Is (from prior milestones)

| Technology | Version | Status |
|------------|---------|--------|
| FastAPI | 0.115.12 | KEEP |
| SQLAlchemy asyncio | 2.0.40 | KEEP |
| asyncpg | 0.30.0 | KEEP |
| pandas | 2.2.3 | KEEP — critical for all new analytics |
| numpy | 1.26.4 | KEEP — critical for all new analytics |
| scipy | 1.13.1 | KEEP — already installed, covers correlation |
| yfinance | 0.2.54 | KEEP — also source for tavan/taban detection |
| ta | 0.11.0 | KEEP — covers ADX, Bollinger for regime engine |
| APScheduler | 3.11.0 | KEEP |
| XGBoost | 2.1.4 | KEEP |
| openai | >=1.82.0 | KEEP — Gemini via compatible client |
| diskcache | 5.6.3 | KEEP — caching layer |
| vaderSentiment | any | **REMOVE** — replaced by Turkish NLP (see below) |

---

## New Additions — v7.0 Specific

### 1. Turkish NLP Sentiment — Replace vaderSentiment

**Decision: `savasy/bert-base-turkish-sentiment-cased` via `transformers` pipeline — loaded lazily, CPU-only, cached.**

**The problem with VADER:** VADER is English-rule-based. Turkish morphology makes it useless for Turkish financial news (KAP announcements, Borsa Istanbul news). A stock with "zarar" (loss) scores neutral or positive in VADER.

**Options evaluated:**

| Option | Pip installable | Offline capable | RAM (inference) | Status |
|--------|-----------------|-----------------|-----------------|--------|
| `savasy/bert-base-turkish-sentiment-cased` | Yes (via `transformers`) | Yes (after first download) | ~400MB model + ~800MB runtime | ACTIVE, 100M downloads |
| `zemberek-python` | Yes (`pip install zemberek-python`) | Yes | ~50MB | ABANDONED — last release 2022, Snyk: inactive; no sentiment output, morphology only |
| multilingual-BERT (`bert-base-multilingual-cased`) | Yes (via `transformers`) | Yes | ~700MB model | Not sentiment fine-tuned for Turkish; generic NLU only |
| `emre/turkish-sentiment-analysis` | Yes (via `transformers`) | Yes | ~400MB model | Smaller community, fewer downloads |
| `TurkishBERTweet` | Yes (via `transformers`) | Yes | ~400MB model | Social media Turkish, not financial text |

**Why savasy/bert-base-turkish-sentiment-cased wins:**
- Largest Turkish NLP community adoption (savasy maintains the canonical Turkish BERT NLP pipeline)
- Based on `dbmdz/bert-base-turkish-cased` (BERTurk), specifically fine-tuned for sentiment
- Works fully offline after first `from_pretrained()` download — cache in `/app/models/`
- Standard transformers pipeline API — integrates with existing `transformers==4.51.3` already in stack (the prior STACK.md recommended removing transformers, but v7.0 re-introduces it for this specific use case)
- CPU inference is viable: 100-300ms per news headline on CPU (acceptable for batch processing, not on-demand)

**Critical constraint:** The model loads ~400MB on disk, ~800MB in RAM at inference time. This **must be lazy-loaded** — not at server startup. Load on first sentiment analysis request and keep in memory for the process lifetime. This means the Railway service needs to handle a one-time memory spike on first call.

**Lazy loading pattern:**
```python
_sentiment_pipeline = None

def get_sentiment_pipeline():
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        from transformers import pipeline
        _sentiment_pipeline = pipeline(
            "text-classification",
            model="savasy/bert-base-turkish-sentiment-cased",
            device=-1,  # CPU
        )
    return _sentiment_pipeline
```

**Do NOT load at APScheduler startup** — only trigger when a sentiment batch job runs (e.g., post-market KAP digest).

**KAP announcement classification:** Use `savasy/bert-turkish-text-classification` for multi-class topic classification (dividends, capital increase, financials, etc.) — same model family, same lazy-load pattern.

| Package | Version | Install |
|---------|---------|---------|
| `transformers` | 4.51.3 (already in stack) | Already installed |
| `torch` | 2.6.0 (already in stack — CPU only) | Already installed |

**Note:** Prior STACK.md recommended removing transformers + torch. v7.0 reverses this — keep them, but ensure CPU-only torch is used (no CUDA dependency pulls in on Railway). The existing `torch==2.6.0` line in requirements.txt should be `torch==2.6.0+cpu` or use `--extra-index-url https://download.pytorch.org/whl/cpu` to avoid GPU variant size.

**Net new pip packages:** 0 (transformers + torch already in requirements.txt)
**Confidence: HIGH** — Model card verified on HuggingFace, API is standard transformers pipeline.

---

### 2. Market Regime Engine — Rule-Based (ADX + Bollinger Width)

**Decision: Rule-based using existing `ta` library — NO new package needed.**

**Options evaluated:**

| Approach | Package | Maintainability | Railway RAM | Retraining needed |
|----------|---------|-----------------|-------------|-------------------|
| HMM | `hmmlearn==0.3.3` | LOW — HMM states are unstable across windows; needs constant label calibration | +30MB | YES — regime labels shift as new data arrives |
| Rule-based | `ta` (existing) | HIGH — deterministic, debuggable, no model state | 0 | NO |
| Rolling statistics | pandas (existing) | HIGH — volatility percentile + return sign is transparent | 0 | NO |
| ML clustering | scikit-learn (existing) | MEDIUM — requires feature engineering and label assignment | 0 | YES (periodic) |

**Why rule-based wins for this project:**

HMM sounds sophisticated but has a critical problem for a personal tool: the hidden states are unlabeled. A 3-state HMM assigns states 0, 1, 2 — which one is "bull"? You must manually inspect each retrain to relabel. This is fragile maintenance work. More importantly, hmmlearn 0.3.3 (released Oct 2024) is in "limited-maintenance mode" — the maintainers have flagged it as not actively developed.

Rule-based regime detection using ADX + Bollinger Band Width is used by professional trading desks for exactly this scenario: deterministic, auditable, no retraining.

**Implementation using existing `ta` library:**

```python
# Uses: ta==0.11.0 (already in requirements.txt)
# Uses: pandas==2.2.3 (already in requirements.txt)

from ta.trend import ADXIndicator
from ta.volatility import BollingerBands

def detect_regime(df: pd.DataFrame) -> str:
    """
    Returns: 'bull' | 'bear' | 'sideways' | 'volatile'
    Input df: must have 'High', 'Low', 'Close' columns.
    """
    adx = ADXIndicator(df['High'], df['Low'], df['Close'], window=14)
    bb = BollingerBands(df['Close'], window=20, window_dev=2)

    current_adx = adx.adx().iloc[-1]
    bb_width = bb.bollinger_wband().iloc[-1]  # bandwidth as % of middle band
    price_vs_sma = (df['Close'].iloc[-1] / df['Close'].rolling(50).mean().iloc[-1]) - 1

    # ADX > 25: trending. < 20: ranging.
    if bb_width > 0.15 and current_adx < 20:
        return 'volatile'
    elif current_adx >= 25 and price_vs_sma > 0.02:
        return 'bull'
    elif current_adx >= 25 and price_vs_sma < -0.02:
        return 'bear'
    else:
        return 'sideways'
```

Thresholds (ADX 20/25, BB width 0.15, price 2%) are calibrated for daily BIST data — adjust per backtesting phase.

**Net new pip packages:** 0
**Confidence: HIGH** — ADX + Bollinger width for regime is well-documented pattern; `ta` library already covers both indicators.

---

### 3. Sector-Specific Fundamental Metrics — Manual Calculation

**Decision: Manual calculation from yfinance data — NO new library.**

**No Python library covers Turkish financial standards (BDDK/SPK reporting).** Turkish bank NIM (Net Interest Margin), NPL (Non-Performing Loan) ratios, and GYO NAV discount calculations require Turkish regulatory disclosure formats (KAP), which no generic library understands.

**Data availability from yfinance for BIST:**
- yfinance `Ticker.financials` and `Ticker.balance_sheet` return Turkish company data with Yahoo Finance's standardized field names — unreliable for sector-specific ratios
- For Banks: NIM and NPL are not in yfinance — must be scraped from KAP quarterly reports or computed from BDDK published data
- For GYO (REITs): NAV requires summing property valuations from annual reports — not in yfinance
- For Holdings: NAV discount requires cross-referencing subsidiary market caps (available via yfinance for listed subsidiaries)

**Recommended approach per sector:**

| Sector | Available via yfinance | Manual calculation required |
|--------|----------------------|----------------------------|
| Banks (GARAN, ISCTR, etc.) | totalRevenue, netIncome, totalAssets | NIM = Net Interest Income / Avg. Earning Assets (from KAP scrape); NPL requires BDDK data |
| GYO (ISGYO, EKGYO, etc.) | bookValue, marketCap | NAV discount = (Book Value - Market Cap) / Book Value (proxy — use bookValue as NAV proxy when KAP data unavailable) |
| Holdings (KCHOL, SAHOL, etc.) | Subsidiary market caps via individual tickers | Sum listed subsidiary market caps × ownership %; compare to holding market cap |

**What to build:** A `SectorScoringAdapter` class per sector that wraps the existing `ScoringEngine` and overrides weights:
- Banks: weight technical less, weight NIM/NPL-proxy ratios more
- GYO: add NAV discount metric, reduce growth metrics
- Holdings: add conglomerate discount metric

Use `Ticker.info['sector']` from yfinance to route to the correct adapter.

**Net new pip packages:** 0
**Confidence: MEDIUM** — yfinance coverage of Turkish sector-specific metrics is partial; the NAV discount calculation for GYO and Holdings is achievable but NIM/NPL for banks requires KAP scraping which is separate work.

---

### 4. Portfolio Analytics — Beta + Correlation Matrix

**Decision: Use `numpy` + `scipy` + `pandas` already in stack. Add `empyrical-reloaded` for beta.**

**Correlation matrix:** `pandas.DataFrame.corr()` is sufficient and zero-cost — already in stack. For 100 stocks, the matrix is 100×100 = 10,000 pairs, trivially fast with pandas.

**Beta calculation:**

`scipy.stats.linregress(stock_returns, index_returns)` gives beta as the slope coefficient — already in stack (scipy==1.13.1). This is the simplest and most interpretable approach.

**Alternatively:** `empyrical-reloaded` provides `beta(returns, benchmark_returns)` as a one-liner with annualization and edge case handling:

```python
# pip install empyrical-reloaded
from empyrical import beta
portfolio_beta = beta(portfolio_daily_returns, bist100_daily_returns)
```

empyrical-reloaded (maintained fork of Quantopian's empyrical, latest 0.5.12, actively maintained in 2025) requires numpy>=1.9.2 and scipy>=0.15.1 — both satisfied. It also provides Sharpe ratio, max drawdown, Calmar ratio — useful for the backtest quality work in v7.0.

**Decision: Add `empyrical-reloaded`** — the beta function handles edge cases (NaN, alignment, annualization) that manual scipy.linregress requires you to handle separately. Package is small (~2MB installed, no new system dependencies).

| Package | Version | Install |
|---------|---------|---------|
| `empyrical-reloaded` | >=0.5.12 | `pip install empyrical-reloaded` |

**Net new pip packages:** 1 (empyrical-reloaded)
**Confidence: HIGH** — scipy already in stack; empyrical-reloaded is actively maintained; beta calculation is standard.

---

### 5. Backtesting with Slippage + Commission

**Decision: `backtesting.py` — lightweight, pandas-native, no system dependencies.**

**Options evaluated:**

| Library | Slippage support | Commission support | RAM | Complexity | Railway compatible |
|---------|-----------------|-------------------|-----|------------|-------------------|
| `backtesting.py` | YES (spread parameter) | YES (commission=) | ~15MB installed | LOW | YES |
| `vectorbt` | YES | YES | ~80MB + numba JIT | HIGH | RISKY — numba compilation on cold start |
| `bt` | YES (commission function) | YES | ~30MB | MEDIUM | YES |
| manual pandas | Manual | Manual | 0 | HIGH (error-prone) | YES |
| `backtrader` | YES | YES | ~20MB | HIGH (event-loop model) | YES |

**Why backtesting.py:**
- Smallest installed footprint (~15MB, pure Python)
- `Backtest(data, Strategy, commission=0.001, spread=0.002)` covers BIST realistic costs out of the box (Borsa Istanbul: ~0.1% commission per leg + ~0.2% bid-ask spread for mid-cap)
- pandas DataFrames as input — zero data conversion from existing yfinance pipeline
- No system library dependencies (vectorbt requires numba which JIT-compiles on first run — cold start penalty on Railway is prohibitive)
- Actively maintained: GitHub shows 2024-2025 commits

**Regime-based signal performance analysis** (v7.0 requirement): filter backtest results by the regime labels from the Market Regime Engine above — backtesting.py exposes trade-by-trade results as a DataFrame, making this a pandas groupby operation.

**BIST-specific slippage model:**
```python
# BIST realistic parameters (2026)
# Thinly traded stocks: higher spread
# Liquid BIST30: ~0.05% spread
Backtest(
    data,
    Strategy,
    commission=0.001,   # 0.1% — Borsa Istanbul standard commission (per side)
    spread=0.002,       # 0.2% — mid-cap BIST spread proxy (no real bid-ask from yfinance)
    exclusive_orders=True,
)
```

| Package | Version | Install |
|---------|---------|---------|
| `backtesting` | >=0.3.3 | `pip install backtesting` |

**Net new pip packages:** 1 (backtesting)
**Confidence: HIGH** — backtesting.py is well-documented; commission/spread parameters verified from official docs.

---

### 6. Tavan/Taban (Circuit Breaker) Detection

**Decision: Pure calculation from yfinance daily OHLC data — NO new library.**

**How BIST circuit breakers work:**
- Individual stocks: price moves ±10% from previous session's VWAP triggers a tavan (upper) or taban (lower) circuit breaker
- Index-level: BIST100 drops 5% or 7% from session open triggers market halt

**yfinance provides `Close` and `Volume` — no bid-ask, no intraday VWAP.** Tavan/taban detection must be approximated from daily OHLC:

```python
def detect_price_limit(df: pd.DataFrame, threshold: float = 0.095) -> dict:
    """
    Detects if a stock is at or near its daily price limit (tavan/taban).
    Uses previous close as VWAP proxy (conservative — actual VWAP unavailable).
    Returns: {'at_tavan': bool, 'at_taban': bool, 'pct_change': float}
    """
    prev_close = df['Close'].iloc[-2]
    current_close = df['Close'].iloc[-1]
    pct_change = (current_close - prev_close) / prev_close

    return {
        'at_tavan': pct_change >= threshold,   # >=9.5% — approaching 10% limit
        'at_taban': pct_change <= -threshold,
        'pct_change': pct_change,
    }
```

**Limitation:** True BIST tavan/taban uses VWAP of previous session, not closing price. This proxy is accurate for most cases but may misfire on high-volume days where VWAP diverges significantly from close. Flag this in the UI tooltip.

**Net new pip packages:** 0
**Confidence: MEDIUM** — BIST circuit breaker rules are documented (±10% from VWAP); yfinance does not provide intraday VWAP, so the implementation uses close price as proxy. The 9.5% threshold catches stocks approaching (but not yet at) limit.

---

### 7. Liquidity Scoring

**Decision: Derived from yfinance volume data — NO new library, NO external data source.**

**What BIST-specific liquidity data exists beyond yfinance:**
- Borsa Istanbul official data feed: provides 5-level bid/ask depth — but requires a paid data subscription (dxFeed, Bloomberg)
- No free Python library for real-time BIST liquidity metrics exists as of 2026

**What yfinance provides that IS useful:**
- Daily volume (Volume column in `download()`)
- Previous volumes (rolling history)
- Market cap (from `Ticker.info`)

**Liquidity score algorithm using existing data:**

```python
def calculate_liquidity_score(df: pd.DataFrame, info: dict) -> dict:
    """
    Liquidity score 0-100 using volume-based proxies.
    Higher = more liquid (easier to trade without slippage impact).
    """
    avg_volume_20d = df['Volume'].rolling(20).mean().iloc[-1]
    volume_consistency = 1 - (df['Volume'].rolling(20).std().iloc[-1] / avg_volume_20d)
    market_cap = info.get('marketCap', 0)

    # Thinly traded: avg daily volume < 1M TRY notional
    avg_price = df['Close'].rolling(20).mean().iloc[-1]
    avg_daily_notional = avg_volume_20d * avg_price  # TRY

    score = 0
    if avg_daily_notional > 100_000_000:   # >100M TRY/day: very liquid
        score += 50
    elif avg_daily_notional > 10_000_000:  # >10M TRY/day: liquid
        score += 30
    elif avg_daily_notional > 1_000_000:   # >1M TRY/day: moderate
        score += 10
    # else: thinly traded — score 0

    score += min(30, int(volume_consistency * 30))  # consistency bonus (max 30)
    score += min(20, int(min(market_cap / 1e10, 1) * 20))  # market cap bonus (max 20)

    return {
        'liquidity_score': min(100, score),
        'avg_daily_notional_try': avg_daily_notional,
        'is_thinly_traded': avg_daily_notional < 1_000_000,
        'volume_consistency': round(volume_consistency, 2),
    }
```

**Note on spread proxy:** Amihud illiquidity ratio (|return| / volume) is a standard academic proxy for bid-ask spread when market depth data is unavailable — this is the appropriate addition to the score above for a "spread proxy" metric.

**Net new pip packages:** 0
**Confidence: MEDIUM** — Volume-based liquidity proxies are academically validated (Amihud 2002); absence of real bid-ask data is the main limitation. The thresholds (1M/10M/100M TRY notional) are calibrated to BIST market structure as of 2026.

---

## What NOT to Add (v7.0)

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `hmmlearn` | Hidden states require manual relabeling after every retrain; limited-maintenance since Oct 2024 | Rule-based ADX + Bollinger (zero maintenance) |
| `zemberek-python` | Abandoned (last release 2022); provides morphology only, not sentiment | `savasy/bert-base-turkish-sentiment-cased` |
| `vectorbt` | numba JIT compilation on Railway cold start adds 60-120s penalty; memory-hungry | `backtesting.py` |
| `bt` library | Heavier than backtesting.py; strategy API is more complex for no benefit at this scale | `backtesting.py` |
| `backtrader` | Event-loop model requires significant code restructuring; no maintenance since 2023 | `backtesting.py` |
| `empyrical` (original) | Quantopian abandoned it; numpy 2.x compatibility issues | `empyrical-reloaded` |
| Real-time BIST data feeds | Require paid subscriptions (dxFeed, Bloomberg); out of budget | yfinance volume proxies |
| GPU-accelerated transformers | Railway has no GPU; CUDA install bloats image by 4GB | CPU-only inference (device=-1) |
| `LangChain` or LLM orchestration | Overkill; Gemini direct API already working | Existing Gemini service |
| `pyfolio` | Heavy dependency; empyrical-reloaded covers the needed metrics subset | `empyrical-reloaded` |

---

## Net New Dependencies (v7.0)

**Backend (pip) — only 2 new packages:**
```bash
pip install empyrical-reloaded>=0.5.12 backtesting>=0.3.3
```

**transformers + torch:** Already in requirements.txt — reinstate them (prior STACK.md recommended removal; v7.0 Turkish NLP requires them). Pin CPU-only torch:
```bash
# In requirements.txt:
torch==2.6.0
--extra-index-url https://download.pytorch.org/whl/cpu
```

**Frontend:** No new packages for v7.0 features (all computation is backend-side).

---

## Memory Budget Assessment (Railway Free Tier)

| Component | RAM at rest | RAM at peak | When |
|-----------|------------|-------------|------|
| FastAPI + uvicorn | ~80MB | ~80MB | Always |
| PostgreSQL driver pool | ~20MB | ~20MB | Always |
| XGBoost model loaded | ~50MB | ~50MB | After first prediction |
| Turkish BERT sentiment | 0 (lazy) | ~800MB | Only during KAP batch job |
| Market Regime Engine | 0 (computed) | ~10MB | During analysis request |
| empyrical-reloaded | ~5MB | ~5MB | During portfolio analysis |
| backtesting.py | ~15MB | ~50MB | During backtest run |
| **Base total** | ~170MB | ~170MB | Normal operation |
| **With BERT active** | ~170MB | **~970MB** | BERT inference window |

**Risk:** BERT inference peak (~970MB) exceeds the Railway $5-credit free tier's 512MB limit. Mitigations:
1. Run BERT sentiment as a scheduled job (APScheduler, post-market 18:30) — not on-demand
2. Unload model after batch completes: `del _sentiment_pipeline; import gc; gc.collect()`
3. Consider Railway Hobby plan ($5/month, 8GB RAM) if memory OOMs are observed — the LLM value justifies the cost

**All other v7.0 features (regime detection, portfolio analytics, backtesting, tavan/taban, liquidity) are negligible memory additions.**

---

## Version Compatibility Summary

| Package | Version | Python 3.9 | Notes |
|---------|---------|------------|-------|
| `empyrical-reloaded` | >=0.5.12 | YES | Requires numpy>=1.9.2 (satisfied: 1.26.4) |
| `backtesting` | >=0.3.3 | YES | Pure Python; Bokeh for visualization (optional) |
| `transformers` | 4.51.3 | YES | Already in stack; CPU-only inference |
| `torch` | 2.6.0 (CPU) | YES | Already in stack; add `+cpu` build variant |
| `ta` | 0.11.0 | YES | Already in stack; ADX + Bollinger available |
| `scipy` | 1.13.1 | YES | Already in stack; beta via linregress available |
| `pandas` | 2.2.3 | YES | Already in stack; correlation, liquidity calcs |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Turkish NLP | `savasy/bert-base-turkish-sentiment-cased` | `zemberek-python` | Abandoned 2022; no sentiment output |
| Turkish NLP | `savasy/bert-base-turkish-sentiment-cased` | `multilingual-BERT` | Not fine-tuned for sentiment; lower accuracy |
| Regime detection | Rule-based (ADX + BB, `ta` lib) | `hmmlearn` | Requires manual relabeling per retrain; limited maintenance |
| Backtesting | `backtesting.py` | `vectorbt` | numba cold-start on Railway; memory-heavy for parameter sweeps |
| Portfolio beta | `empyrical-reloaded` | `scipy.stats.linregress` (manual) | empyrical handles NaN/alignment edge cases cleanly |
| Liquidity data | yfinance volume proxy | BIST paid data feed | Requires paid subscription; no budget |
| Sector metrics | Manual calculation | Turkish financial library | None exists for BDDK/SPK format |

---

## Sources

- [savasy/bert-base-turkish-sentiment-cased — HuggingFace](https://huggingface.co/savasy/bert-base-turkish-sentiment-cased) — model card, parameter count, inference API, HIGH confidence
- [zemberek-python — Snyk health](https://snyk.io/advisor/python/zemberek-python) — inactive project status confirmed, HIGH confidence
- [hmmlearn — PyPI](https://pypi.org/project/hmmlearn/) — v0.3.3 Oct 2024, limited-maintenance mode, HIGH confidence
- [empyrical-reloaded — PyPI](https://pypi.org/project/empyrical-reloaded/) — v0.5.12, actively maintained fork, HIGH confidence
- [backtesting.py — official docs](https://kernc.github.io/backtesting.py/) — commission/spread parameters, HIGH confidence
- [Railway pricing — official docs](https://docs.railway.com/reference/pricing/plans) — 512MB / 1GB RAM limits, MEDIUM confidence (plan-dependent)
- [Borsa Istanbul circuit breaker rules](https://www.dailysabah.com/business/finance/borsa-istanbul-to-implement-trading-curb-on-index-basis) — ±10% individual stock limits, HIGH confidence
- [dxFeed BIST coverage](https://dxfeed.com/coverage/turkey/) — confirms 5-level bid/ask available only via paid feed, HIGH confidence
- [QuantStart — HMM regime detection](https://www.quantstart.com/articles/market-regime-detection-using-hidden-markov-models-in-qstrader/) — HMM limitations for production, MEDIUM confidence

---

*Stack research for: Stalize v7.0 — Analiz Kalitesi & Sistem Bütünlüğü*
*Researched: 2026-05-14*
