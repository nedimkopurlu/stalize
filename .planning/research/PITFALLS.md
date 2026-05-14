# Pitfalls Research

**Domain:** BIST-specific analysis features added to existing Turkish stock assistant (v7.0)
**Researched:** 2026-05-14
**Confidence:** HIGH — pitfalls are grounded in actual codebase state, confirmed yfinance GitHub issues, BDDK data structure, and Turkish NLP research literature

---

## Critical Pitfalls

### Pitfall 1: Turkish NLP BERT Model Breaks Railway 512MB RAM Constraint

**What goes wrong:**
`dbmdz/bert-base-turkish-cased` (BERTurk) loads approximately 440MB of weights into RAM at inference time. On Railway's free tier (512MB), this leaves only ~70MB for FastAPI, SQLAlchemy sessions, APScheduler's 8 jobs, and pandas DataFrames. The process is OOM-killed within minutes of startup, silently restarting without ever logging the failure clearly.

**Why it happens:**
Developers test BERT locally on MacBooks with 16GB RAM where it works fine. The model footprint is only discovered in production when Railway shows repeated restart cycles. `transformers.pipeline("text-classification", model="dbmdz/bert-base-turkish-cased")` loads at module import time — the crash happens before any request is served.

**How to avoid:**
- Do not use full BERTurk. Use one of: (a) `distilbert-base-turkish-cased` (~250MB, 40% faster), (b) rule-based Turkish keyword sentiment dictionary + Zemberek morphological analysis (~5MB), or (c) call Gemini 2.0 Flash for batch sentiment on KAP texts (already authenticated, no extra memory cost, 1500 calls/day free).
- The recommended path for this system: Gemini batch sentiment. The model is already in use, already authenticated, and Türkçe is rated "mükemmel" in the project decision log. One Gemini call can classify a batch of 10 KAP announcements for ~$0.00 on free tier.
- If a local model is required, guard the load with a try/except and `ENABLE_LOCAL_NLP=false` env flag so the service starts in keyword-fallback mode when RAM is insufficient.
- Never load any transformer model at module import time. Lazy-load inside a function so APScheduler and FastAPI start before the model footprint hits.

**Warning signs:**
- Railway deployment shows repeated restarts with exit code 137 (OOM).
- Memory metric in Railway dashboard hits ceiling immediately after `uvicorn` startup.
- `transformers` or `torch` appears in `requirements.txt` — current `requirements.txt` does NOT include either; adding them would triple the dependency footprint.

**Phase to address:** Turkish NLP migration phase — before implementation, decide on Gemini batch sentiment vs. rule-based. Defer any local BERT model consideration to a future milestone with upgraded hosting.

---

### Pitfall 2: yfinance P/E and P/B for BIST Stocks Are USD-Denominated, Not TRY

**What goes wrong:**
Yahoo Finance reports `trailingPE`, `priceToBook`, `marketCap`, `totalRevenue`, and `netIncomeToCommon` for `.IS` suffix stocks in USD (converted at the Yahoo spot rate), while the actual share price used in scoring is fetched in TRY. The `FundamentalAnalysisEngine._calculate_score()` already has hardcoded `pe < 10 → score += 15` thresholds calibrated for US/global markets. A BIST bank trading at P/E=8 in TRY terms may show P/E=3 in Yahoo's USD terms — scoring it as deeply undervalued when it is fairly valued. The current code at `fundamental.py:103` uses `info.get('trailingPE')` with no currency validation or sanity bounds.

**Why it happens:**
yfinance documentation does not document currency conversion behavior for emerging market stocks. The `.IS` suffix stocks are nominally TRY-denominated but Yahoo normalizes some fields to USD for consistency with its global screener. This is confirmed in GitHub issue #1788 of the yfinance repo (data errors after the 2020 index rebasing) and in the observed behavior of `marketCap` values that are 30x smaller than Borsa Istanbul data for the same stocks.

**How to avoid:**
- Add a sanity layer in `FundamentalAnalysisEngine.analyze_stock()` before scoring:
  - P/E sanity: if `pe < 1.0 or pe > 200`, mark as `None` (outside any plausible BIST range)
  - P/B sanity: if `pb < 0.1 or pb > 50`, mark as `None`
  - `marketCap`: compare against `regularMarketPrice * sharesOutstanding` computed in TRY; if the ratio is not between 0.03 and 0.04 (approximate USD/TRY range), flag as currency-converted
- For the fundamental data quality layer (required in v7.0), add a `data_quality_score` field to `Fundamental` that records how many of the 8 key metrics are present and pass sanity checks. Surface this in the UI so the user knows when scores are computed from 2 metrics vs. 8.
- Cross-reference P/E and P/B against `isyatirim.com.tr` scraped data when yfinance values fail sanity checks. İş Yatırım is already referenced in `data_collector.py` as a data source.

**Warning signs:**
- `marketCap` in the Fundamental table is ~30x smaller than the company's actual market cap in TRY.
- All BIST banks score as "deeply undervalued" (P/E < 5) when actual P/E in TRY is 7-9.
- `fundamental_score` is always near 80-100 for BIST100 banks regardless of fundamentals quality.

**Phase to address:** Fundamental data quality layer phase — must precede sector-specific scoring so the scoring algorithms receive validated inputs.

---

### Pitfall 3: Sector-Specific Scoring Silently Breaks Existing Score Normalization

**What goes wrong:**
The current `ScoringEngine` produces scores in 0-100 via `_calculate_score()` which is globally normalized. When bank-specific scoring (NIM, NPL, CAR) is added, those bank metrics have different ranges (NIM is 2-8%, NPL is 1-5%, CAR is 12-20%) and will produce raw scores on different scales than the existing P/E/P/B/ROE path. If the sector-specific path skips some of the 6 universal scoring components and the sector-specific components are on different scales, the 0-100 normalization breaks — bank stocks will cluster at extreme scores (very high or very low) compared to industrials, making cross-sector comparison meaningless.

**Why it happens:**
Adding sector branches to a scoring engine that was designed without sector awareness is a refactor that touches normalization, not just logic. Developers add sector-specific metrics as additive bonuses on top of the universal score without accounting for the fact that banks legitimately have high debt-to-equity (it is a structural feature of banking, not a risk indicator) which the current code penalizes at `debt_to_equity > 150 → score -= 10`.

**How to avoid:**
- Define a sector override map before writing any scoring code: which universal metrics are EXCLUDED for each sector, and what sector-specific metrics REPLACE them.
  - Banks: exclude `debt_to_equity` (structurally high); replace with NIM, NPL ratio, CAR
  - GYO: exclude `revenue_growth` (lumpy); replace with NAV discount, dividend yield
  - Holdings: exclude `operating_margin` (consolidated distorts); replace with NAV discount to market
- The sector detection must use `settings.BIST100_SECTORS` dict, which already maps symbols to sector names. Do NOT add sector logic based on company name string matching.
- Cap the sector-specific score adjustments so the total remains in 0-100. The bank scoring path must sum to the same maximum as the industrial path.
- Add a per-stock `scoring_method` field to the API response (`"universal"`, `"bank"`, `"gyo"`, `"holding"`) so the UI can show the user which scoring method was applied.

**Warning signs:**
- After adding bank scoring, all bank stocks score > 85 or all score < 40.
- Cross-sector rankings show banks and GYOs dominating top 10 with scores that cannot be compared to industrial stocks.
- `ISBANK` and `GARAN` both score 95 despite meaningful differences in NPL and NIM.

**Phase to address:** Sector-specific scoring phase — after fundamental data quality layer so validated inputs are available.

---

### Pitfall 4: Market Regime Engine Misidentifies BIST Regimes Due to Nominal vs. Real Returns

**What goes wrong:**
Standard HMM (Hidden Markov Model) or volatility-based regime detection is calibrated on nominal returns. In Turkey's high-inflation environment (2022-2024: 60-85% annual CPI), nominal BIST100 returns were strongly positive even during economic contractions. A regime engine trained on nominal data classifies the BIST as "bull market" throughout 2022 even though USD-adjusted returns were deeply negative. This causes the regime engine to label inflationary bear markets as bullish, and deflationary corrections as bearish, inverting the signal for an investor thinking in real or USD terms.

**Why it happens:**
Global regime detection literature uses US/EU market data where inflation is 2-3% and nominal ≈ real returns. Porting these methods to Turkey without inflation adjustment produces systematically wrong classifications.

**How to avoid:**
- Compute regime on USD-adjusted BIST100 returns, not TRY returns. USD/TRY rate is already collected via yfinance (`TRY=X` or `USDTRY=X`).
- Alternatively, use a multi-signal regime: BIST100 TRY return + VIX-equivalent (BIST volatility index if available) + TCMB policy rate direction. The TCMB rate is already fetched by `data_collector.py`.
- Use a simple rule-based regime detector before considering HMM — BIST regime can be approximated by: BIST100 50-day MA trend direction + BIST100 20-day rolling volatility level + TCMB rate direction. This avoids the HMM training data requirement.
- Never label a regime as "bull" purely from nominal TRY price appreciation without cross-referencing USD-adjusted returns or real interest rate environment.

**Warning signs:**
- Regime engine labels 2022 (high inflation, economic crisis) as "bull market."
- Regime signals produce the same label for 12+ consecutive months with no transitions.
- Regime-based signal filtering improves backtest on US data but degrades BIST backtest.

**Phase to address:** Market Regime Engine phase — the regime engine must be tested against 2022-2024 BIST data where the inflation-distortion effect is most visible.

---

### Pitfall 5: Tavan/Taban Detection Has 20% Rule Exception That Breaks Simple Threshold Logic

**What goes wrong:**
The naive approach is: if `(close - prev_close) / prev_close >= 0.20`, the stock is at tavan. This is wrong. BIST's actual circuit breaker regime is: individual stocks have a +/- 20% daily limit, but WHEN a session-wide circuit breaker is triggered (at -10% index level), trading halts and reopens — meaning a stock can open at its previous tavan price and move another 20% from THERE in the reopened session. Additionally, stocks subject to "volatility-based continuous auction" (the "borsa yoğunluğu" system) can be temporarily moved to a different trading model where the 20% rule is replaced by a price band determined by the last auction price. Simple threshold logic misclassifies these cases as "still has room" when the stock is actually circuit-broken.

**How to avoid:**
- Compute tavan/taban relative to the day's theoretical equilibrium price (`teorik eşleşme fiyatı`), not the previous close. The theoretical equilibrium price is the weighted average of orders at the matching price in the order collection phase.
- A simpler, less error-prone approach: flag any stock where `abs(daily_change_pct) > 18.5%` as "possible tavan/taban" and add a UI indicator. The 18.5% threshold (not 20%) accounts for rounding at the exchange level. Treat this as an advisory indicator, not a hard calculation.
- Source the tavan/taban status from Borsa Istanbul's live data (BloombergHT/Foreks API already fetched in `data_collector.py` as `LiveBistQuote`) which includes `high` and `low` fields — if `high == low` and both equal `last_price`, the stock has not moved from its limit price, which is a strong indicator of tavan/taban.

**Warning signs:**
- Tavan detection misses stocks that opened at yesterday's tavan (they moved 20% from a price that was already the previous day's tavan).
- During high-volatility days (2023 banking crisis, 2024 election), many stocks show `daily_change_pct` of exactly 20% but the indicator does not fire.

**Phase to address:** Data quality features phase — alongside liquidity scoring, as both require reliable daily OHLCV data from the BloombergHT/Foreks source already in the system.

---

### Pitfall 6: Portfolio Beta Calculation Is Unstable on Short BIST History Windows

**What goes wrong:**
Standard beta calculation uses `cov(stock_returns, index_returns) / var(index_returns)` over a rolling window. For BIST stocks, 90-day windows (the most common choice) frequently produce betas of 2.0-4.0 during high-volatility periods and 0.2-0.6 during quiet periods for the SAME stock. This instability makes portfolio-level beta (sum of weighted betas) meaningless — it swings between "very aggressive" and "very defensive" week to week without actual portfolio changes, confusing the user.

**Why it happens:**
BIST exhibits higher-frequency regime switches than developed markets due to political events (elections, central bank decisions, geopolitical events), and the correlation structure of BIST100 stocks is more unstable than S&P500 stocks. A 90-day window that works for US stocks captures too many regime transitions for BIST.

**How to avoid:**
- Use a 252-day (1-year) window for beta calculation as the primary display metric. Stability over 1-year is higher and aligns with how Turkish retail investors think about a stock's behavior.
- Show a 30-day "current regime beta" as a secondary indicator, clearly labeled as "kısa vadeli beta" with a note that it is volatile.
- Clip displayed beta to the range [0, 3] for UI display. Values outside this range on BIST are almost always data artifacts (thin trading, corporate events) rather than genuine systematic risk measurement.
- For portfolio beta: weight-average the 252-day betas of holdings. Do NOT use rolling portfolio beta — it is meaningless when the portfolio composition changes.
- Use `PriceHistory` table (already populated) — avoid re-fetching from yfinance for beta calculations.

**Warning signs:**
- Portfolio beta changes from 1.2 to 2.8 between two consecutive weekly updates with no trades.
- Any individual stock beta exceeds 3.0 (almost certainly a thin-trading artifact).
- Beta for cash-heavy GYO stocks exceeds 1.5 (GYOs should be < 0.8 in normal conditions).

**Phase to address:** Portfolio analysis phase — beta must be validated against 2022-2024 BIST data before exposing in the UI.

---

### Pitfall 7: KAP Classification by Regex on Title Text Fails on Turkish Morphology

**What goes wrong:**
KAP announcement titles are in Turkish and use inflected forms. A naive regex for `"temettü"` (dividend) misses: "temettüyü", "temettüsünü", "kâr payı", "brüt temettü", "temettü avansı". A regex for `"sermaye artırımı"` misses: "sermaye artırımına", "bedelsiz sermaye artırımı", "rüçhan hakkı kullanımı". The KAP RSS title field is short (often 40-60 chars) and uses company-specific abbreviations — `"ÖDA"` for "Özel Durum Açıklaması", `"BK"` for "Bağımsız Kurul", etc. Pattern-based classifiers built on Western financial NLP assumptions miss 30-40% of relevant announcements.

**Why it happens:**
Developers write regex for the obvious forms they know. Turkish agglutination (a single word can be 8+ morphemes) means that testing on 10 sample announcements gives false confidence — the real KAP feed has hundreds of morphological variants.

**How to avoid:**
- Use KAP's own `disclosure_type` field from the API response, not the title text. The KAP disclosure API (already at `settings.KAP_DISCLOSURE_API_URL`) returns a structured `disclosureType` field with normalized type codes (e.g., `FRY` for financial results, `TEM` for dividends). Use these codes, not regex on text.
- When the disclosure type code is missing (RSS fallback path), use stem matching: check if the normalized title contains any of: `temett` (stem of all dividend forms), `sermay` (capital), `kamuoy` (public announcement), `malî` or `mali` (financial). Do NOT try to match inflected forms.
- Use the `_normalize_text` method already in `KAPParser` which strips diacritics — this is the right foundation; apply stem matching on top of it.
- Build the classification taxonomy from KAP's actual type codes first. Request the full list from `kap.org.tr/tr/api/disclosure/types` before writing any classification logic.

**Warning signs:**
- More than 20% of KAP announcements are classified as "Diğer" (other/unknown).
- Dividend announcements from `ARCLK` and `THYAO` are not detected during earnings season.
- The KAP feed for a day with 50+ announcements produces < 10 classified events.

**Phase to address:** KAP classification phase — research the KAP API type code taxonomy first, implement code-based classification, regex on title text only as a last-resort fallback.

---

### Pitfall 8: Backtest Slippage Without BIST-Specific Parameters Produces Overoptimistic Results

**What goes wrong:**
Generic slippage models use 0.05-0.10% per trade (US market assumption). BIST100 liquid names (THYAO, GARAN, EREGL) have typical spreads of 0.05-0.15%, but BIST100 includes stocks in the 30-100 rank that have spreads of 0.3-1.0% and thin order books. A backtest that applies uniform 0.1% slippage dramatically overestimates the profitability of signals on illiquid names. BIST also has a commission structure: Borsa Istanbul charges 0.005% (maker) and 0.01% (taker) per side, plus brokerage adds 0.05-0.15% depending on broker — total round-trip costs of 0.15-0.35% for liquid names, 0.5-2.0% for illiquid.

**Why it happens:**
Developers copy-paste slippage parameters from US backtesting examples without researching BIST-specific market microstructure. The resulting backtest looks profitable but the strategy loses money in live trading due to transaction cost drag.

**How to avoid:**
- Use a tiered slippage model based on the stock's liquidity tier:
  - BIST30 names: 0.10% slippage + 0.20% commission (round trip)
  - BIST30-100 rank 30-70: 0.20% slippage + 0.25% commission
  - BIST100 rank 70-100: 0.40% slippage + 0.30% commission
- Source liquidity tiers from the `liquidity_score` feature being built in the same milestone — use it to parametrize backtest costs rather than hardcoding.
- Use the `volume` field from `PriceHistory` to detect thin-trading days: if signal date has `volume < 7-day average * 0.3`, flag the backtest trade as "may not have been fillable."
- Never backtest without commission. Zero-commission is not available on BIST — even discount brokers charge minimum 0.05%.

**Warning signs:**
- Backtest Sharpe ratio > 3.0 for signals that apply to all 100 BIST stocks equally.
- Backtest win rate > 60% for all market conditions including 2022 bear market.
- Backtest uses the same `slippage_bps` for ALARK (BIST rank ~80) and THYAO (BIST rank 2).

**Phase to address:** Backtest enhancement phase — tiered slippage model must be implemented before any strategy performance is shown in the UI.

---

### Pitfall 9: Liquidity Score Uses Volume Without Adjusting for Turkish Market Half-Sessions

**What goes wrong:**
BIST operates two sessions daily: morning (10:00-12:30) and afternoon (14:00-17:30). On Fridays and religious holidays, only the morning session runs, and some holidays close the exchange early. A liquidity score based on 30-day average volume that includes these half-session days will be systematically underestimated for all stocks — they look 30-40% less liquid than they are because half-session volumes are half of normal. Additionally, BIST has a pre-session order collection phase (09:30-10:00) whose volume is separate from the continuous session volume.

**Why it happens:**
yfinance returns daily volume aggregates without flagging partial trading days. A developer computing 30-day average volume on raw yfinance data inadvertently includes these low-volume days.

**How to avoid:**
- Before computing volume-based liquidity metrics, filter `PriceHistory` to exclude dates where `volume < 0.3 * 30_day_mean_volume` (a heuristic for half-session days, since genuine thin-trading days should fail the thinly-traded test anyway).
- Alternatively: fetch Turkish market calendar to identify half-session and holiday dates. Use the `exchange_calendar` package (`exchange_calendars` on PyPI), which includes `XIST` (Istanbul Stock Exchange) calendar.
- The liquidity score should be computed from: (a) 30-day median daily turnover (not mean — median is more robust to outliers), (b) average bid-ask spread proxy (`(high - low) / close` as a crude spread estimate), (c) percentage of days with `volume > minimum_viable_volume` threshold.

**Warning signs:**
- All BIST stocks show sudden volume drop on Fridays in the liquidity time series.
- Stocks with obviously thin trading (small-caps outside BIST30) score similarly to BIST30 blue chips on liquidity.
- Liquidity scores computed in May differ significantly from those computed in June due to Kurban Bayramı holiday cluster.

**Phase to address:** Data quality / liquidity scoring phase — market calendar filtering is a prerequisite before any volume-based computation.

---

### Pitfall 10: GYO NAV Discount Cannot Be Calculated from yfinance Data Alone

**What goes wrong:**
NAV discount for Turkish GYOs (Real Estate Investment Trusts) requires the independently appraised portfolio value, which is reported in quarterly KAP filings (not daily market data). yfinance provides market cap and book value but not the independently appraised real estate portfolio value — the book value for a GYO at cost is not the same as the appraised portfolio value (which can differ by 20-50%). Attempting to compute NAV discount as `(market_cap - book_value) / book_value` will produce systematically wrong discounts.

**Why it happens:**
GYO NAV methodology is specific to Turkish real estate investment structures and requires KAP-filed financial statement data (specifically the "gayrimenkul değerleme raporu" — real estate appraisal report). This is fundamentally different from US REIT NAV which can be approximated from quarterly SEC filings.

**How to avoid:**
- For the MVP sector scoring, use a proxy metric instead of true NAV discount: `price_to_book` (already available via yfinance) as a GYO valuation indicator, clearly labeled as "defter değeri oranı" (not "NAV iskontosu") in the UI.
- True NAV discount computation requires scraping GYO-specific KAP financial filings. Defer this to a future milestone and document the current limitation.
- For GYO scoring, weight dividend yield (available via yfinance) more heavily than the NAV metric — dividend yield is a reliable and accessible metric for GYO quality assessment.
- Add a note in the UI for GYO stocks: "NAV iskonto hesabı henüz desteklenmiyor. Defter değeri oranı gösterilmektedir."

**Warning signs:**
- GYO `fundamental_score` values look identical to industrial stock scores.
- `priceToBook` for TRGYO or EKGYO shows values < 1.0 which are then labeled as "NAV discount" — this is incorrect (it is market-to-book, not market-to-appraised-NAV).

**Phase to address:** Sector-specific scoring phase (GYO) — define what is achievable with available data, document what requires future work.

---

### Pitfall 11: APScheduler Memory Leak from jitter Parameter Crashes Railway on New Jobs

**What goes wrong:**
The current `main.py` scheduler has 8 jobs. Adding new jobs for regime engine updates, liquidity scoring refreshes, and KAP classification runs will increase APScheduler's overhead. APScheduler 3.x has a documented memory leak in `_apply_jitter()` that causes 35GB+ virtual memory allocations when `jitter` is combined with frequent job intervals. If any of the new jobs are added with `jitter` parameter (commonly copy-pasted from job examples), Railway's 512MB container is OOM-killed within hours.

**Why it happens:**
APScheduler docs show `jitter=30` as a reasonable parameter in examples. The memory leak only manifests at scale with many jobs and frequent intervals.

**How to avoid:**
- Never use `jitter` in any `add_job` call. The fix is already documented: remove `jitter` from ALL scheduler job registrations.
- Use `coalesce=True, max_instances=1` on every job — this prevents backlog accumulation which is the secondary cause of memory growth.
- Set `misfire_grace_time=3600` on all jobs.
- For staggered execution (to avoid all jobs running simultaneously on startup), use fixed `start_date` offsets per job rather than `jitter`. Example: regime engine at `start_date=datetime.now() + timedelta(minutes=2)`, liquidity at `timedelta(minutes=4)`.
- Monitor job count — if total jobs exceed 12, evaluate whether some jobs should be merged into one consolidated "daily analytics" job.

**Warning signs:**
- Railway memory metric climbs continuously and never stabilizes after adding new jobs.
- Scheduler shows backlog of missed job runs in logs.
- New jobs added with `trigger='interval', seconds=300, jitter=30` pattern.

**Phase to address:** Every phase that adds a new background job — establish the no-jitter convention as a code review standard before writing any scheduler registration.

---

### Pitfall 12: Position Sizing Guidance Shows Dangerously Large Sizes on High-Scoring BIST Stocks

**What goes wrong:**
A naive Kelly Criterion implementation with estimated win rate from backtest signal data will recommend position sizes of 20-40% of portfolio for high-scoring BIST stocks during bull regimes. For a concentrated personal portfolio (the user's case: single user, BIST100, personal tool), this creates concentrated single-stock risk that is inappropriate even for the best-signal stocks. BIST also has gaps and halts that make large positions harder to exit — tavan/taban situations can lock a position for multiple days.

**Why it happens:**
Kelly Criterion assumes infinite divisibility and continuous liquidity. The Kelly fraction (edge / odds) produces large sizes when backtest win rates are high — but backtest win rates on in-sample BIST data are routinely overestimated (no out-of-sample test, look-ahead bias common in hand-built backtests).

**How to avoid:**
- Use fractional Kelly (half-Kelly or quarter-Kelly) as the default. Half-Kelly captures ~75% of Kelly growth with half the volatility.
- Hard caps: no single position recommendation > 10% of portfolio, regardless of Kelly output.
- Liquidity gate: if the stock's `liquidity_score` is below a threshold (thinly traded), cap the position recommendation further (e.g., max 5%).
- Frame all sizing guidance as educational ranges, not precise recommendations. The UI should say "Bu skor seviyesinde tipik pozisyon: %3-%7" not "Önerilen pozisyon: %6.2".
- Never backtest-derived Kelly sizing without an out-of-sample validation period. Use 2019-2021 as in-sample, 2022-2024 (the volatile period) as validation.

**Warning signs:**
- Position sizing UI recommends > 15% for any single stock.
- Sizing recommendations do not decrease for thinly-traded BIST100 names (rank 70-100).
- Kelly formula input uses in-sample backtest win rate without a haircut.

**Phase to address:** Position sizing phase — implement with conservative defaults and hard caps before any portfolio guidance is shown in the UI.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Using `priceToBook` as GYO "NAV discount" | Calculation available immediately | Systematically wrong metric labeled incorrectly, erodes user trust | Only if clearly labeled "defter değeri oranı, NAV değil" in UI |
| Uniform slippage (0.1%) across all BIST stocks | Simple implementation | Backtest overstates alpha for BIST rank 70-100 stocks | Never in final backtest display — always tier by liquidity |
| VADER on Turkish text as temporary bridge | No code change required | Positive sentiment on Turkish text that VADER does not understand, feeds wrong signal into scoring | Never — remove VADER or gate it behind a flag immediately |
| Including half-session days in volume average | No calendar dependency | Liquidity scores systematically underestimated on Fridays and post-holiday periods | Never — add exchange_calendars or simple volume-based day filter |
| Gemini batch sentiment (10 announcements per call) | Saves API quota | Risk of classification errors from context bleed between announcements in same batch | Acceptable with max_batch=5 and explicit per-item JSON response format |
| yfinance P/E without sanity bounds | Zero extra code | Corrupted fundamental scores for 20-30% of BIST stocks due to USD/TRY currency error | Never — sanity bounds are 5 lines of code |
| APScheduler `jitter` on new jobs | Staggered execution | OOM crash on Railway within hours | Never on Railway free tier |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| yfinance `.info` for BIST fundamentals | Using `marketCap` directly as TRY market cap | Always divide by approximate USD/TRY rate or compare against `regularMarketPrice * sharesOutstanding` |
| yfinance `.history()` for beta calculation | Using `Adj Close` which applies USD dividend adjustments | Use `Close` column for BIST stocks — `Adj Close` adjustments are applied inconsistently for `.IS` suffix stocks |
| KAP disclosure API | Hitting the API without respecting rate limits (already 5-min scan) | Add an exponential backoff on HTTP 429; the existing `kap_parser.py` already has `record_source_failure` — use it before retrying |
| TCMB rate data for regime engine | Using the weekly TCMB rate bulletin (delayed by 5 days) as a real-time signal | Use the policy rate decision date from TCMB, not the bulletin date — TCMB decisions are pre-announced and move markets before the bulletin |
| BloombergHT/Foreks live quote (LiveBistQuote) | Treating `as_of` as market close time | BloombergHT quotes are delayed 15 minutes during trading hours; `as_of` is the quote fetch time, not market close |
| Gemini batch sentiment | Sending all 50 KAP announcements in one prompt | Gemini free tier has 32k context limit; batch max 5-8 KAP titles with classification instruction |
| `exchange_calendars` XIST calendar | Calendar shows half-sessions as full trading days | `exchange_calendars.get_calendar("XIST")` correctly handles Turkish half-sessions, but verify against Borsa Istanbul official calendar for Islamic holidays which shift annually |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Computing 100×100 correlation matrix per request | `/api/correlation/matrix` times out | Cache with 6-hour TTL; recompute only on scheduler job | Immediately — correlation matrix is O(n²) on 252-day return arrays |
| Computing beta for all 100 stocks on every portfolio page load | Portfolio page takes 8-15 seconds | Pre-compute betas in a scheduled job, store in `Fundamental` or a new `RiskMetrics` table | From first real user request |
| Turkish NLP inference per KAP announcement in real-time | KAP scan job takes 5+ minutes, misses next 5-minute trigger | Batch Gemini calls; process max 20 announcements per scan job | On any day with > 10 KAP announcements |
| Loading full `PriceHistory` for all 100 stocks into memory for liquidity scoring | OOM on Railway 512MB | Process stocks in batches of 20; compute and persist liquidity score to DB | Immediately on first full computation |
| Multi-timeframe technical analysis (daily + weekly + monthly) per request | Technical analysis endpoint takes 3-5 seconds | Pre-compute in background job, cache in `Recommendation` table | When all three timeframes are computed on each API call |

---

## BIST-Specific Dangerous Assumptions

These assumptions are common from global financial analysis but are wrong for BIST:

| Assumption | Why It Fails on BIST | Correct BIST-specific Truth |
|------------|---------------------|---------------------------|
| "P/E < 10 is undervalued" | In high-inflation Turkey, P/E is compressed — P/E of 6-9 is normal for BIST banks in 2023-2024 | Sector-normalize P/E; BIST bank P/E 6-9 is fair value, not deep value |
| "Nominal returns capture market direction" | 2022 BIST TRY return: +50%; USD return: -30% | Always provide USD-adjusted return alongside TRY return for regime analysis |
| "Dividend yield > 5% is attractive" | With Turkish inflation at 60%, a 5% dividend yield is deeply negative in real terms | Flag dividend yields that are below CPI as "reel getiri negatif" |
| "High debt-to-equity is negative" | BIST banks have D/E > 1000% by definition (deposits are liabilities) | Exclude D/E from bank scoring entirely |
| "Volume confirms breakouts" | BIST has structured auctions and frequent circuit breakers that create artificial volume spikes | Exclude circuit-breaker days from volume confirmation logic |
| "GYO book value ≈ asset value" | Turkish REITs must get properties appraised annually; appraised value can be 2x book cost | Never use book value as NAV proxy without flagging the methodology |
| "Beta is stable across regimes" | BIST beta is highly unstable due to political event frequency | Show beta confidence range alongside point estimate |

---

## "Looks Done But Isn't" Checklist

- [ ] **Turkish NLP:** Verify no transformer model loads at startup — check `requirements.txt` for `transformers` and `torch` absence; confirm sentiment path uses Gemini batch or keyword rules
- [ ] **Fundamental data quality:** Verify `pe_ratio` sanity bounds are enforced — confirm no BIST stock has `pe < 1.0` or `pe > 200` in the `Fundamental` table after data quality layer runs
- [ ] **Bank scoring:** Verify `debt_to_equity` is excluded from bank fundamental score — confirm `GARAN.IS` and `ISCTR.IS` use bank-specific scoring path, not universal path
- [ ] **Market regime:** Verify regime is not purely nominal — confirm USD-adjusted BIST100 return is used as input; check that 2022 is classified as mixed/bear, not bull
- [ ] **Tavan/taban detection:** Verify threshold is 18.5% not 20% — confirm detector fires on day after a tavan day when stock reopens at tavan price
- [ ] **Portfolio beta:** Verify beta uses 252-day window — confirm short-window (30-day) beta is labeled "kısa vadeli" and clipped to [0, 3]
- [ ] **KAP classification:** Verify disclosure type code is used before regex — confirm classification of "TEM" type codes works without regex fallback
- [ ] **Backtest slippage:** Verify tiered slippage is applied — confirm BIST30 names use different slippage than BIST100 rank 70-100 names
- [ ] **Liquidity score:** Verify half-session days are excluded — confirm Friday volumes are filtered before 30-day average computation
- [ ] **Position sizing caps:** Verify hard cap enforced — confirm no single stock recommendation exceeds 10% of portfolio regardless of Kelly output
- [ ] **APScheduler new jobs:** Verify no `jitter` parameter — check all new `add_job` calls in `main.py` for absence of `jitter=` argument

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| BERT loaded on Railway → OOM crash | LOW (no data loss) | Remove model from requirements.txt; switch to Gemini batch; redeploy |
| Corrupted fundamental scores from USD P/E | MEDIUM | Add sanity bounds; re-run `analyze_stock` for all 100 symbols; `UPDATE fundamental SET fundamental_score = NULL WHERE pe_ratio < 1.0` then recompute |
| Bank stocks scored with universal D/E penalty for extended period | MEDIUM | Identify affected date range in `Recommendation` history; re-score bank sector symbols; notify user of score revision |
| Regime engine labels 2022 as bull (backtest distortion) | HIGH (backtest results are misleading) | Rebuild regime using USD-adjusted returns; invalidate all historical backtest performance stored in DB; rerun backtest |
| Tavan/taban fires on every 19%+ move (too sensitive) | LOW | Adjust threshold; no data migration needed |
| KAP classifier misses 30% of dividend announcements | MEDIUM | Switch to KAP API type codes; re-classify stored `NewsItem` records by re-fetching and reclassifying the last 30 days of announcements |
| Backtest results shown with 0.1% slippage then corrected to tiered | MEDIUM | Re-run backtest with corrected slippage; update displayed metrics; add prominent note that results were revised |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Turkish NLP memory (BERTurk OOM) | Turkish NLP / Sentiment phase | `requirements.txt` has no `transformers` or `torch`; sentiment uses Gemini batch |
| yfinance P/E USD corruption | Fundamental data quality layer phase | No stock has `pe_ratio < 1.0` in Fundamental table; `data_quality_score` field present |
| Sector scoring normalization breaks | Sector-specific scoring phase | Bank stocks use `scoring_method="bank"` in API response; scores in 0-100 for all sectors |
| Market regime nominal vs. real | Market Regime Engine phase | 2022 classified as mixed/bear when using USD-adjusted returns |
| Tavan/taban edge cases | Data quality features phase | 18.5% threshold; next-day-at-tavan detection verified in unit test |
| Portfolio beta instability | Portfolio analysis phase | 252-day window used; beta clipped to [0, 3]; out-of-range values logged |
| KAP classification regex misses | KAP classification phase | API type code taxonomy implemented; regex only as last-resort fallback |
| Backtest slippage overoptimism | Backtest enhancement phase | Tiered slippage by liquidity tier; commission included; visible in backtest methodology note |
| Liquidity half-session distortion | Liquidity scoring phase | Exchange calendar or volume filter applied before average computation |
| GYO NAV unavailable from yfinance | Sector-specific scoring phase (GYO) | `priceToBook` labeled as "defter değeri oranı" not "NAV"; user-facing note in UI |
| APScheduler jitter OOM | Every phase adding background jobs | No `jitter=` in any `add_job` call; validated by grep in CI |
| Position sizing oversized Kelly | Position sizing phase | Hard cap of 10% enforced; half-Kelly default used; sizing labeled as guidance not recommendation |

---

## Sources

- yfinance GitHub issue #1788 — Turkish BIST data after 2020 index rebasing: [Turkish BIST stockmarket index data and some stocks data after dividend is incorrect](https://github.com/ranaroussi/yfinance/issues/1788)
- APScheduler memory leak — jitter issue: [Memory leak when worker raises an exception #235](https://github.com/agronholm/apscheduler/issues/235) and [litellm fix PR #15846](https://github.com/BerriAI/litellm/pull/15846)
- BERTurk model: [dbmdz/bert-base-turkish-cased on Hugging Face](https://huggingface.co/dbmdz/bert-base-turkish-cased) — model weight size ~440MB confirmed
- BDDK Turkish banking sector NIM/NPL data: [Turkish Banking Sector Main Indicators](https://www.bddk.org.tr/BultenAylik/en/Home/HaberBulteni) — quarterly updates only, not daily
- Turkish GYO NAV discount research: [Why do Turkish REITs trade at discount to net asset value? — Empirical Economics, Springer](https://link.springer.com/article/10.1007/s00181-020-01846-y)
- BIST circuit breaker thresholds: [BIST'ten flaş karar! Devre kesici yüzde 10'a çekildi — Sözcü, 2020](https://www.sozcu.com.tr/2020/ekonomi/bistten-flas-karar-devre-kesici-yuzde-10a-cekildi-5676729/)
- Regime detection in high-inflation markets: [Regime-Switching Factor Investing with Hidden Markov Models — MDPI 2020](https://www.mdpi.com/1911-8074/13/12/311)
- Kelly Criterion limitations: [Analysis of The Kelly Criterion in Practice — Alpha Theory](https://www.alphatheory.com/blog/kelly-criterion-in-practice-1)
- Turkish NLP state of the art: [Turkish sentiment analysis: A comprehensive review — Sigma Yıldız 2024](https://sigma.yildiz.edu.tr/storage/upload/pdfs/1722849273-en.pdf)
- KAP public disclosure platform: [kap.org.tr/en/about/general-information](https://kap.org.tr/en/about/general-information)
- Existing codebase: `backend/app/services/fundamental.py`, `backend/app/services/kap_parser.py`, `backend/app/services/data_collector.py`, `backend/app/core/config.py`, `backend/app/main.py` — direct code inspection 2026-05-14

---
*Pitfalls research for: BIST 100 AI investment advisor (Stalize) — v7.0 BIST analysis quality milestone*
*Researched: 2026-05-14*
