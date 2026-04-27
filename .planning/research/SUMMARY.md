# Research Summary: Stalize — BIST 100 AI Investment Advisor

**Synthesized:** 2026-04-16
**Confidence:** HIGH

---

## Executive Summary

Stalize is a brownfield refactor of a personal AI investment advisor for BIST 100. The core stack (FastAPI + PostgreSQL + Next.js + DeepSeek) is locked. The refactor adds four targeted capabilities: LLM response streaming via SSE, structured AL/SAT/TUT output via the `instructor` library, a two-layer caching system to prevent yfinance rate-limit failures, and XGBoost model persistence to eliminate a critical event-loop-blocking bug. Three large unused dependencies (tensorflow, torch, transformers — 3-4GB total) must be removed immediately.

**Approach: repair-before-feature.** The codebase has four confirmed critical defects that silently corrupt all analytical output before any new features are added:
1. KAP data falls back to mock announcements without any alert
2. XGBoost retrains synchronously on every scheduler run (blocks event loop for minutes)
3. Scoring weights defined in two places — config.py values are silently ignored
4. Timestamps mix naive local time with UTC

---

## Recommended Stack Additions

| Library | Purpose | Why |
|---------|---------|-----|
| `instructor` | Structured DeepSeek output (Pydantic) | DeepSeek doesn't support `json_schema`; instructor retries on malformed JSON automatically |
| `requests-cache` | yfinance HTTP caching | TTL-based; zero code changes in data_collector.py; prevents 429s |
| `diskcache` | Computed results cache | LLM analysis (30min TTL), technical indicators (5min), fundamentals (24h) |
| Vercel AI SDK (`useChat`) | SSE chat frontend | Eliminates ~300 lines of boilerplate; official FastAPI streaming template exists |

**Remove immediately:** `tensorflow==2.19.0`, `torch==2.6.0`, `transformers==4.51.3`, `sentencepiece` — 3-4GB, zero usage in codebase.

---

## Key Feature Findings

**The gap is real and unoccupied.** Fintables and StocKeys are strong data tools but require users to do all analytical synthesis. No existing BIST 100 tool:
- Generates an AI morning briefing (pre-synthesized narrative, not a data dump)
- Does 3-layer contradiction detection (fundamental vs price vs sentiment conflict)
- Has causal macro-to-stock linkage (TCMB decision → sector → individual stock)

**Table stakes (must have):**
- Reliable KAP feed (no mock fallback)
- Accurate real-time BIST prices with volume
- Clean fundamental ratios (P/E, P/B, debt)
- Technical indicators (RSI, MACD, Bollinger)
- Macro indicators (USD/TRY, faiz, enflasyon)

**Differentiators (this project's unique value):**
- AI pre-generated morning briefing with narrative synthesis
- 3-layer contradiction detection: "Temel güçlü ama fiyat düşüyor → neden?"
- Causal graph: macro event → sector impact → stock effect
- AL/SAT/TUT with explicit risk/reward reasoning, not just a score

---

## Architecture Decisions

**Two new services, zero modifications to existing services:**
- `BriefingService` — reads from DB tables (Stock, NewsItem, MacroIndicator), generates narrative, stores in `DailyBriefing` model
- `ChatService` — assembles context from DB, calls DeepSeek with streaming, appends to `ChatMessage` log

**Critical:** Never call existing service singleton methods (scoring_engine, technical_engine) from chat/briefing endpoints. Read from DB columns only — re-running analysis pipelines at request time would be catastrophically slow.

**Streaming pattern:** FastAPI `StreamingResponse` with `text/event-stream` + Vercel AI SDK `useChat`. SSE (not WebSocket) — data is 15-min delayed anyway, real-time socket adds zero value.

**Briefing pre-generation:** APScheduler cron at 06:30 weekdays. Dashboard `GET /api/briefing/today` returns DB row in <10ms. Never generate at request time (LLM takes 5-15s).

**Temperature by use case:**
- Sentiment analysis: `0.2` (existing, correct)
- Chat conversation: `0.3`
- Structured 3-layer analysis JSON: `0.1`

---

## Critical Pitfalls

| Pitfall | Risk | Phase to Fix |
|---------|------|-------------|
| KAP mock fallback in production | Silent fake data → wrong LLM analysis | Phase 1 |
| XGBoost trains on every call | Blocks async event loop, streaming gaps | Phase 2 |
| Scoring weights diverged (config vs service) | Config has zero effect on runtime | Phase 1 |
| DeepSeek no rate limiter | Budget exhaustion on high-news days | Phase 3 |
| LLM context timestamp not validated | Stale data presented as current | Phase 3 |
| `indirect_impact = 0` hardcoded | Exclude from LLM context until implemented | Phase 4+ |

---

## Recommended Phase Order

1. **Foundation Repair** — Fix 4 silent data-corruption defects + split endpoints.py + remove unused deps
2. **ML Persistence + Caching** — XGBoost to disk, requests-cache + diskcache layer
3. **LLM Infrastructure** — instructor, semaphore rate limiter, token cap, prompt freshness validation, SSE sentinel pattern
4. **AI Daily Briefing** — BriefingService + DailyBriefing model + APScheduler cron + dashboard
5. **Conversational Chat** — ChatService + ChatMessage model + SSE endpoint + frontend chat page

---

## Open Questions for Requirements Phase

- What is the acceptable daily DeepSeek token budget? (affects rate limiter design)
- Should `indirect_impact` in event fusion be excluded from LLM context entirely until implemented?
- Is conversation history persistence needed across browser sessions, or ephemeral is fine?
- KAP news sector classification: does kap_parser.py currently classify by sector?

---
*Synthesized: 2026-04-16*
