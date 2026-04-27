# Feature Research

**Domain:** Personal AI investment advisor — BIST 100 (Turkish stock market)
**Researched:** 2026-04-16
**Confidence:** HIGH for table stakes and differentiators; MEDIUM for competitor comparison (limited Turkish-market tooling data)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features a personal AI stock analysis tool must have. Missing any of these makes the product feel broken, not just incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Real-time (or near-real-time) price data | Any tool without current prices is useless for decisions | LOW | yfinance polling every 5 min is sufficient; no WebSocket needed |
| KAP news feed with filtering | KAP is the primary official news source for all BIST-listed companies; competitors Fintables, StocKeys both build on this | LOW | Already built — KAPParser + APScheduler at 5 min intervals |
| Stock-level recommendation (AL/SAT/TUT) | Users open a tool to get a decision, not raw data | MEDIUM | Already have scoring engine; just needs surfacing cleanly in UI |
| Fundamental indicators per stock | P/E, PD/DD, revenue growth, debt ratio — baseline for any analysis | LOW | yfinance provides; already stored in `Fundamental` model |
| Technical signals | Trend, RSI, MACD, moving averages — expected by any investor | MEDIUM | `technical.py` service exists; needs validation it's correct |
| Macro context | TCMB rate, USD/TRY, inflation — Turkish market is uniquely macro-sensitive | MEDIUM | TCMB + TUIK scrapers exist; need reliable data flow |
| Search / stock lookup | User must be able to reach any BIST 100 ticker quickly | LOW | Can be a simple dropdown or chat command |
| Explanation behind recommendation | "Why AL?" — without this, recommendation is just a number | MEDIUM | LLM synthesis layer; the differentiating part is the quality of explanation |
| Reliable data (not mock fallback) | KAP mock fallback currently active in prod — this kills trust in all outputs | HIGH | Must fix before any feature work; data integrity is foundation |

### Differentiators (Competitive Advantage)

Features that distinguish Stalize from Fintables, StocKeys, and generic AI tools. These are where the tool creates real value and where the existing codebase has unique leverage.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| AI daily morning briefing | Pre-synthesized market picture the moment you open the app — no assembly required; QuantHub shows demand for this pattern | HIGH | New build; needs: scored stocks + KAP digest + macro summary + LLM narrative layer |
| 3-layer contradiction detection (Fundamental vs Technical vs Sentiment) | "Strong fundamentals, falling price — why?" is where real opportunities hide; no BIST tool does this explicitly | HIGH | Core differentiator; requires all three scores to be reliable first |
| Causal chain analysis (macro → sector → stock) | "If TCMB raises rates, which BIST stocks are hit?" — unique to Stalize; no competitor has this | HIGH | `causal.py` + `knowledge_graph.py` exist; surface in chat and briefing |
| Conversational stock deep-dive via chat | Free-form "tell me about THYAO" triggers structured 3-layer analysis, not just a data dump | HIGH | New build; needs intent detection + structured prompt template + streaming response |
| Turkish macro-aware scoring | Enflasyon, kur, faiz politikası baked into the score — not a US-market generic model | MEDIUM | Existing scoring weights partially do this; needs alignment between `config.py` and `scoring.py` |
| ML price-direction signal as one input (not the headline) | XGBoost prediction honest about confidence, not oversold as "price target" | MEDIUM | `ml.py` exists; needs model persistence so it's fast; present as "model signal" not "forecast" |
| Sector-level KAP news digests in briefing | "3 KAP haberi bu sabah finans sektörünü etkiliyor" — contextualizes noise | MEDIUM | Requires KAP news classification by sector; LLM can do this |
| Risk/reward framing (not just direction) | "Risk yüksek ama ödül 3x" vs "Düşük risk, küçük yukarı" — decision quality over raw signal | MEDIUM | Needs explicit risk/reward output format from LLM; scoring engine provides sub-scores as inputs |

### Anti-Features (Deliberately NOT Building)

Features that seem useful but add complexity, risk, or distraction without proportional value at this scope.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Automated trade execution (broker API) | "Let AI trade for me" | Legal liability, broker API complexity, catastrophic failure risk for real money; explicitly out of scope | Clear AL/SAT/TUT + risk/reward so user makes the call |
| Real-time WebSocket price streaming | "I want tick-by-tick prices" | BIST is volatile intraday but Stalize's value is in synthesis, not speed; polling every 5 min is sufficient; WebSocket adds infra complexity with no analytical benefit | 5-min APScheduler polling is fine for personal use |
| Portfolio P&L tracker | "Show me my gains/losses" | Requires broker integration or manual entry maintenance; no auth, no multi-account support; v1 priority is analysis quality, not portfolio accounting | Manual watchlist for stocks of interest; full portfolio tracking is v2+ |
| Multi-stock comparison table (screener) | "Show me top 10 AL stocks sorted by score" | Screener UX is a separate product mode; it conflicts with the focused briefing-first approach; Fintables already does this well | Rankings endpoint already exists; surface top N in briefing instead of building a screener |
| Price alerts / push notifications | "Notify me when THYAO hits X" | No mobile, no push infrastructure, no background notification service; adds backend complexity for marginal gain on a personal tool | Scheduled morning briefing covers the "what happened" need |
| Social / sharing features | "Share my analysis" | Single-user personal tool; social layer is a different product category | Not applicable |
| Technical charting (candlestick UI) | "Show me the chart" | TradingView, Fintables already do this excellently; building charts in Next.js is high cost for low differentiation | Link to TradingView for the ticker; focus on textual AI analysis |
| Backtesting UI | "Test my strategy" | Backtesting script exists (`backtester.py`) but surfacing it as UI is a full feature; not core to daily advisory use | Keep as dev script; surface backtest confidence in ML signal label |
| OAuth / multi-user auth | "Let others use it" | Out of scope; single-user personal tool; adding auth creates maintenance burden | No auth; localhost access is the security boundary |

---

## Feature Dependencies

```
[Reliable Data Pipeline]
    └──required by──> [AI Morning Briefing]
    └──required by──> [3-Layer Stock Analysis]
    └──required by──> [AL/SAT/TUT Recommendation]
    └──required by──> [Contradiction Detection]

[ML Model Persistence]
    └──required by──> [ML Score as Briefing Input]
    └──required by──> [3-Layer Analysis: ML Layer]

[Scoring System Alignment (config.py == scoring.py)]
    └──required by──> [Reliable AL/SAT/TUT]
    └──required by──> [Contradiction Detection]

[KAP News + Sector Classification]
    └──required by──> [AI Morning Briefing: News Digest]
    └──required by──> [Chat: "What KAP news affects X?"]

[3-Layer Scoring (Fundamental + Technical + Sentiment all reliable)]
    └──required by──> [Contradiction Detection]
    └──required by──> [Risk/Reward Output]

[AI Morning Briefing]
    └──enhances──> [Chat Interface]
        (briefing creates context; chat lets user drill in)

[Causal Chain Analysis]
    └──enhances──> [AI Morning Briefing]
        (macro events → sector impact narrative)
    └──enhances──> [Chat Interface]
        (user asks "if faiz artarsa ne olur?")

[Chat Interface]
    └──conflicts with──> [Screener/Comparison Table]
        (chat-first means user asks for rankings; building a separate screener UI duplicates the same job)
```

### Dependency Notes

- **Reliable Data Pipeline required by everything:** Mock KAP fallback is a trust-killer. Data integrity is the zero-layer — all analytical features built on bad data will produce wrong recommendations. Must fix before any new feature work.
- **ML Model Persistence required by briefing and chat:** Retraining XGBoost on every call makes chat unusable (latency) and briefing unreliable (timing). Persist models to disk; reload on startup.
- **Scoring alignment required by contradiction detection:** If `config.py` and `scoring.py` weights differ, the "contradiction" between layers might be an artifact of misconfiguration, not a real signal. Fix alignment before building contradiction UI.
- **Briefing enhances chat:** Users will read the morning briefing, then use chat to drill into specific items. The briefing creates the frame; chat completes the thought. Design the briefing to invite follow-up questions.
- **Chat conflicts with screener:** Building both a conversational interface and a traditional screener table UI creates UX confusion about which to use. Pick one interaction model. Chat wins because it's the differentiator.

---

## MVP Definition

### Launch With (v1)

Minimum to validate the core value: "Open app, get your BIST 100 picture, drill into any stock."

- [ ] **Reliable data pipeline** — KAP real data (no mock fallback), yfinance prices stable, TCMB/TUIK flowing — without this, nothing else matters
- [ ] **AI daily briefing page** — top movers, top/bottom 5 scored stocks, KAP news digest (LLM-summarized by sector), macro snapshot (USD/TRY, TCMB rate, CPI), AI narrative paragraph tying it together
- [ ] **Scoring system alignment** — `config.py` weights match `scoring.py`; sub-scores (fundamental, technical, sentiment, causal, ml) are trustworthy
- [ ] **ML model persistence** — persist XGBoost to disk; load on startup; retrain on schedule (daily), not on every request
- [ ] **Chat interface with structured stock analysis** — user types "THYAO analiz" → LLM produces 3-layer structured output (Fundamental status / Technical status / Sentiment status / Contradiction if any / Karar: AL·SAT·TUT / Risk-Ödül)
- [ ] **Clean, focused UI** — briefing page as home, chat accessible from every page, stock detail surfaceable from briefing

### Add After Validation (v1.x)

Features to add once the core loop works and feels trustworthy.

- [ ] **Contradiction highlighting in briefing** — flag top 3 stocks where fundamental-technical-sentiment diverge significantly; "Dikkat: TEMEL güçlü ama teknik zayıf" callout cards
- [ ] **Causal event cards in briefing** — "TCMB faiz kararı: Finans sektörü -%2.1 baskı altında" surfacing causal chain outputs in human language
- [ ] **Chat memory within session** — "bir önceki hisseyle karşılaştır" — simple in-session context so follow-up questions work
- [ ] **Stock watchlist** — user pins 5-10 tickers; briefing leads with those before broader market view

### Future Consideration (v2+)

Defer until v1 is proven.

- [ ] **Portfolio P&L tracking** — needs broker integration or persistent manual input; high complexity, low MVP priority
- [ ] **Historical briefing archive** — "dünkü brifing neydi?" — useful but requires briefing persistence; defer until briefing generation is stable
- [ ] **Alerts / scheduled Telegram message** — push delivery of morning briefing to Telegram; useful for "open without opening browser" but adds infra
- [ ] **Backtesting UI** — surface `backtester.py` results in dashboard; dev tool today, user feature later

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Reliable data pipeline (no mock fallback) | HIGH | MEDIUM | P1 |
| Scoring system alignment | HIGH | LOW | P1 |
| ML model persistence | HIGH | LOW | P1 |
| AI daily briefing page | HIGH | HIGH | P1 |
| Chat with structured stock analysis | HIGH | HIGH | P1 |
| Clean UI (briefing-first) | HIGH | MEDIUM | P1 |
| Contradiction detection in briefing | HIGH | MEDIUM | P2 |
| Causal event cards in briefing | MEDIUM | MEDIUM | P2 |
| Chat session memory | MEDIUM | MEDIUM | P2 |
| Stock watchlist | MEDIUM | LOW | P2 |
| Historical briefing archive | LOW | MEDIUM | P3 |
| Portfolio P&L tracker | LOW | HIGH | P3 |
| Telegram delivery | MEDIUM | LOW | P3 |

**Priority key:**
- P1: Must have for launch — core value loop
- P2: Adds depth after core is working
- P3: Nice to have; defer until v1 proven

---

## Competitor Feature Analysis

| Feature | Fintables (TR) | StocKeys (TR) | Generic AI tools (Incite, TradingKey) | Stalize Approach |
|---------|---------------|---------------|--------------------------------------|-----------------|
| KAP news | Filtered feed, sector-based | Not primary focus | No (US-market focused) | LLM-summarized digest per sector in briefing |
| Fundamental analysis | Scorecard (Karne), ratios | Deep ratio analysis | Available but US-only data | yfinance fundamentals + LLM narrative |
| Technical analysis | Charts + indicators | Limited | Pattern recognition | Signals used as one sub-score layer |
| Macro integration (TCMB, TUIK) | Economic calendar (passive) | Not present | Not present | Active scoring input via causal graph — unique |
| AI recommendation | None — data only | None — data only | Buy/sell signals (US stocks) | AL/SAT/TUT with 3-layer rationale + risk/reward |
| Contradiction detection | None | None | None | Core differentiator — explicit in every analysis |
| Chat interface | None | None | Available (KeyAI, Incite) | Structured 3-layer output per stock, not generic chat |
| Morning briefing | None (you assemble manually) | None | QuantHub (US, paid) | Automated daily synthesis — core value prop |
| Causal macro → stock analysis | None | None | None | Unique: knowledge_graph traversal surfaced in UX |

**Key finding:** No existing BIST 100 tool combines AI-generated briefing + conversational analysis + causal macro-stock linkage. Fintables and StocKeys are strong data tools but require the user to do all the synthesis. Generic US-market AI tools don't cover KAP or TCMB at all. The gap Stalize fills is real.

---

## Sources

- [Wall Street Zen — AI Stock Analyzers 2026](https://www.wallstreetzen.com/blog/ai-stock-analysis/) — feature survey of leading AI analysis tools
- [Monday.com — Best AI for stock trading 2026](https://monday.com/blog/ai-agents/best-ai-for-stock-trading/) — feature patterns across 12 tools
- [QuantHub Morning Briefing](https://briefing.quanthub.ai/) — reference implementation of AI daily briefing pattern
- [Fintables](https://fintables.com/) — primary Turkish competitor; fundamental analysis + KAP feed
- [StocKeys](https://www.stockeys.com/) — secondary Turkish competitor; fundamental analysis focus
- [GitHub: Borsacı AI Agent](https://github.com/saidsurucu/borsaci) — Turkish-market AI agent reference
- [PMC: Hybrid AI for stock prediction](https://pmc.ncbi.nlm.nih.gov/articles/PMC12191900/) — multi-layer (fundamental + technical + sentiment) framework validation
- [Lyzr: AI Agents for Stock Market](https://www.lyzr.ai/blog/ai-agents-for-stock-market/) — structured analysis output patterns

---

*Feature research for: BIST 100 Personal AI Investment Advisor (Stalize)*
*Researched: 2026-04-16*
