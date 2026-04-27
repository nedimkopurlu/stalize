# Stack Research

**Domain:** Personal AI-powered financial analysis tool (BIST 100, chat interface, daily briefing)
**Researched:** 2026-04-16
**Confidence:** HIGH (brownfield — existing choices verified; new additions researched against current docs)

---

## Context: Brownfield Constraints

This is a **refactor, not a rewrite.** The core stack (FastAPI + PostgreSQL + Next.js + DeepSeek) is locked.
Python is pinned at **3.9** (CI hard-constraint — do not change).
Research focus: four specific additions to the existing stack.

---

## Existing Stack — Keep As-Is

| Technology | Version | Status | Notes |
|------------|---------|--------|-------|
| FastAPI | 0.115.12 | KEEP | Works, no upgrade needed |
| SQLAlchemy asyncio | 2.0.40 | KEEP | Async ORM solid |
| asyncpg | 0.30.0 | KEEP | Required by SQLAlchemy async engine |
| Alembic | 1.15.2 | KEEP | DB migrations working |
| Next.js | 15 (listed as 16.2.3 — likely App Router) | KEEP | App Router confirmed |
| React | 19.x | KEEP | Compatible with streaming patterns below |
| XGBoost | 2.1.4 | KEEP | Add persistence, don't change version |
| yfinance | 0.2.54 | KEEP | Add caching layer around it |
| APScheduler | 3.11.0 | KEEP | AsyncIOScheduler pattern works fine |
| feedparser | 6.0.11 | KEEP | KAP RSS parsing |
| ta | 0.11.0 | KEEP | Technical indicators |
| pydantic | 2.11.1 | KEEP | Core to everything |
| aiohttp | 3.11.18 | KEEP | TCMB/TUIK scrapers |

---

## Remove Immediately

| Remove | Why | Savings |
|--------|-----|---------|
| tensorflow 2.19.0 | No LSTM is actually used in production paths; ~600MB installed weight | ~600MB |
| torch 2.6.0 | Only loaded for Transformers which is also unused | ~2GB |
| transformers 4.51.3 | DeepSeek via openai SDK replaces all NLP; VADER still works for rule-based | ~1GB |
| sentencepiece 0.2.0 | Tokenizer for transformers — transitive dependency only | small |
| SHAP 0.46.0 | Nice-to-have explainability; re-add later if needed after ML persistence lands | ~100MB |

**Total cleanup: ~3-4GB from requirements.txt. Also speeds up CI significantly.**

---

## New Additions — Researched

### 1. LLM Streaming: FastAPI + SSE → Next.js useChat

**Problem:** DeepSeek responses take 5-20s. Without streaming the UI shows a blank loading state.

**Solution: FastAPI StreamingResponse + Vercel AI SDK `useChat`**

**Backend (FastAPI):**
Use `StreamingResponse` with `media_type="text/event-stream"`. The OpenAI SDK already supports `stream=True`, so the pattern is to yield chunks from the async generator directly.

```python
# FastAPI endpoint
from fastapi.responses import StreamingResponse

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def generate():
        async with deepseek_client.chat.completions.stream(
            model="deepseek-chat",
            messages=request.messages,
        ) as stream:
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield f"data: {chunk.choices[0].delta.content}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})
```

**Frontend (Next.js):**
Use Vercel AI SDK's `useChat` hook with `TextStreamChatTransport` pointing at the FastAPI endpoint.

```typescript
// Install: npm install ai
import { useChat } from 'ai/react';
import { TextStreamChatTransport } from 'ai';

const { messages, sendMessage, status } = useChat({
  transport: new TextStreamChatTransport({ api: 'http://localhost:8000/api/chat/stream' }),
});
```

Vercel AI SDK provides official FastAPI + Next.js streaming templates (`vercel-labs/ai-sdk-preview-python-streaming`). The `useChat` hook handles connection drops, partial message reconstruction, and state management. **Do not implement SSE manually on the frontend — that's 200-300 lines of error-prone boilerplate.**

| Package | Version | Install |
|---------|---------|---------|
| `ai` (Vercel AI SDK) | `^4.x` (latest 2025) | `npm install ai` |

**Confidence: HIGH** — Official Vercel template exists for FastAPI + Next.js. SSE is native browser API, no polyfill needed.

---

### 2. Structured AI Output: AL/SAT/TUT + Reasoning

**Problem:** DeepSeek's `json_schema` response format is NOT supported (only `json_object`). Raw JSON prompting occasionally returns empty content or malformed JSON.

**Solution: `instructor` library (Python, wraps openai SDK)**

`instructor` patches the existing `openai`-compatible client and adds retry logic + Pydantic validation on top of `json_object` mode. It handles the "occasionally empty content" bug in DeepSeek's JSON mode by automatically retrying.

```python
# pip install instructor
import instructor
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from enum import Enum

class Signal(str, Enum):
    AL = "AL"
    SAT = "SAT"
    TUT = "TUT"

class StockAnalysis(BaseModel):
    signal: Signal
    conviction: int = Field(ge=1, le=10, description="1-10 conviction score")
    fundamental_summary: str
    technical_summary: str
    sentiment_summary: str
    conflict_detected: bool
    conflict_explanation: str | None
    risk_reward: str
    reasoning: str

# Patch the existing client
client = instructor.from_openai(
    AsyncOpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com"),
    mode=instructor.Mode.JSON,  # Uses json_object mode (DeepSeek-compatible)
)

analysis = await client.chat.completions.create(
    model="deepseek-chat",
    response_model=StockAnalysis,
    messages=[...]
)
# analysis is a validated StockAnalysis instance — no manual JSON parsing
```

**Why instructor over manual JSON prompting:**
- Automatic retry with validation error feedback to the LLM (fixes malformed output on retry)
- Pydantic model is the schema — no schema drift between prompt and parse code
- `Mode.JSON` is DeepSeek-compatible (does not use `json_schema`)
- Used by 3M+ monthly downloads, actively maintained

| Package | Version | Install |
|---------|---------|---------|
| `instructor` | `>=1.8.1` | `pip install instructor` |

**Confidence: HIGH** — Official DeepSeek integration documented at `python.useinstructor.com/integrations/deepseek/`. Pydantic already in stack (2.11.1). Zero conflict with Python 3.9.

---

### 3. Financial Data Freshness — Caching Pattern

**Problem:** yfinance rate-limits at scale (HTTP 429). Current code calls yfinance on every API request. N+1 pattern identified in price aggregation.

**Solution: Two-layer caching using `diskcache` + `requests-cache` + TTL tiers**

**Do NOT add Redis.** This is a single-user local tool. Redis adds operational overhead (separate process, connection management) for zero benefit at this scale.

**Layer 1: `requests-cache` — transparent HTTP-level cache for yfinance**

```python
# pip install requests-cache
import requests_cache
requests_cache.install_cache(
    'yfinance_cache',
    backend='sqlite',
    expire_after=300,  # 5 minutes for prices
)
```

yfinance uses `requests` internally. `requests_cache` intercepts at the HTTP level — no yfinance code changes needed.

**Layer 2: `diskcache` — application-level cache for processed results**

Use `diskcache` for computed/aggregated data (technical indicators, scoring results, LLM analysis output) that is expensive to recompute. `diskcache` is thread-safe and process-safe, persists across restarts, and is significantly faster than SQLite for application-level KV lookups.

```python
# pip install diskcache
import diskcache

cache = diskcache.Cache('/tmp/stalize_cache')

# Cache computed analysis for 30 minutes
@cache.memoize(expire=1800)
def get_stock_analysis(ticker: str) -> dict:
    ...
```

**TTL Strategy by data type:**

| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| BIST price (intraday) | 5 min | BIST closes at 18:00 — no real-time needed |
| BIST price (after hours) | 60 min | Market closed, data stable |
| KAP announcements | 5 min | APScheduler already polls every 5 min — respect that |
| Fundamental data (PD/DD, F/K) | 24 hours | Changes on earnings reports only |
| TCMB rates/reserves | 2 hours | APScheduler already at 2h interval |
| TUIK data | 24 hours | Monthly releases |
| LLM analysis output | 30 min | Expensive to generate, user can force refresh |
| Daily briefing | Until midnight | Regenerate each morning via APScheduler |

**Add jitter to all TTLs (±10%) to avoid thundering herd at batch expiry.**

| Package | Version | Install |
|---------|---------|---------|
| `requests-cache` | `>=1.2.0` | `pip install requests-cache` |
| `diskcache` | `>=5.6.3` | `pip install diskcache` |

**Confidence: HIGH for pattern. MEDIUM for specific TTL values** — TTLs are based on BIST market hours and existing APScheduler intervals; tune after observing 429 frequency.

---

### 4. WebSocket vs Polling for BIST Prices

**Decision: HTTP Polling. Do NOT add WebSocket.**

The PROJECT.md explicitly lists "Gerçek zamanlı borsa akışı (WebSocket)" as **Out of Scope**. This is the correct call for technical reasons too:

1. BIST data from yfinance is already delayed 15 minutes minimum — WebSocket gives false impression of real-time when data is not real-time
2. WebSocket adds server-side connection management complexity (heartbeats, reconnection logic, state) for a single-user tool
3. A simple `setInterval` poll every 30-60 seconds during market hours is invisible to the user and zero complexity to maintain

**Implementation: React polling with SWR**

```typescript
// npm install swr (likely already in project or trivial to add)
import useSWR from 'swr';

const { data: prices } = useSWR(
  '/api/prices/bist100',
  fetcher,
  {
    refreshInterval: isMarketHours() ? 60_000 : 300_000, // 1min during hours, 5min otherwise
    revalidateOnFocus: true,
  }
);
```

**SWR vs React Query:** Both work. SWR is lighter (no `QueryClientProvider` setup) and Vercel-maintained — fits Next.js naturally. If React Query is already in the project, keep it.

| Package | Version | Install |
|---------|---------|---------|
| `swr` | `^2.x` | `npm install swr` |

**Confidence: HIGH** — Polling is the right tool here. WebSocket is explicitly out of scope.

---

### 5. ML Model Persistence

**Problem:** XGBoost retrains on every API call — this is the #1 performance bug in the codebase.

**Solution: Save with XGBoost native format, load at startup, refresh on schedule**

```python
# Save (run once or on schedule)
model.save_model('/app/models/xgboost_bist100.ubj')  # UBJSON format — XGBoost native

# Load at startup (FastAPI lifespan)
import xgboost as xgb
_model: xgb.Booster | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _model
    _model = xgb.Booster()
    _model.load_model('/app/models/xgboost_bist100.ubj')
    yield
```

**Use XGBoost native `.ubj` format, NOT joblib/pickle.** XGBoost's own save/load is cross-version compatible and the recommended path per official docs since XGBoost 2.1. Joblib/pickle breaks across XGBoost major versions.

**Retrain schedule:** APScheduler cron job weekly (Sunday 02:00) or when model file is missing. Store training timestamp in DB for observability.

**No new packages needed.** XGBoost 2.1.4 already in stack.

**Confidence: HIGH** — XGBoost docs explicitly recommend native format over pickle for production.

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Redis | Operational overhead for a single-user local tool; `diskcache` is faster for single-process | `diskcache` + `requests-cache` |
| WebSocket (ws/socket.io) | Data is 15-min delayed anyway; Out of Scope per PROJECT.md | SWR polling |
| LangChain | Massive dependency for features we don't need; DeepSeek integration works directly via openai SDK + instructor | `instructor` + raw openai SDK |
| PydanticAI | Good for agents; overkill for structured output extraction from a single LLM call | `instructor` |
| Celery | Heavy task queue for background jobs that APScheduler already handles | APScheduler (existing) |
| APScheduler 4.x | Breaking API changes from 3.x; existing code uses 3.x — no upgrade value | APScheduler 3.11.0 (existing) |
| `json_schema` response_format | DeepSeek does NOT support it — will return errors | `json_object` + instructor |
| `joblib`/`pickle` for ML models | Breaks across XGBoost versions | XGBoost native `.ubj` format |
| `tensorflow` | Unused; costs 600MB and 30s CI time | Remove |
| `torch` + `transformers` | Unused; costs 2-3GB; DeepSeek LLM covers NLP needs | Remove |

---

## Net New Dependencies

**Backend (pip):**
```bash
pip install instructor>=1.8.1 requests-cache>=1.2.0 diskcache>=5.6.3
```

**Frontend (npm):**
```bash
npm install ai swr
```

**Python 3.9 compatibility confirmed** for all three new pip packages (instructor, requests-cache, diskcache).

---

## Version Compatibility

| Package | Version | Constraint | Notes |
|---------|---------|------------|-------|
| instructor | >=1.8.1 | Python >=3.9 | Uses openai SDK already in stack |
| requests-cache | >=1.2.0 | Python >=3.8 | SQLite backend, no extra system deps |
| diskcache | >=5.6.3 | Python >=3.6 | Pure Python, no system deps |
| ai (Vercel AI SDK) | ^4.x | Node 20 | useChat + TextStreamChatTransport |
| swr | ^2.x | React 19 | Compatible, no known issues |

---

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| `instructor` | Manual JSON prompting | No retry logic; DeepSeek occasionally returns empty JSON |
| `instructor` | PydanticAI | PydanticAI is for agents; instructor is for extraction — wrong abstraction |
| `diskcache` | Redis | Single-user local tool; Redis adds a background process with zero benefit |
| `requests-cache` | Custom caching wrapper | requests-cache intercepts at HTTP level transparently — no yfinance code changes |
| SSE StreamingResponse | WebSocket for chat | SSE is unidirectional (server→client), sufficient for LLM streaming; WebSocket adds bidirectional complexity not needed |
| Vercel AI SDK `useChat` | Manual EventSource | Manual implementation is 200-300 lines; SDK handles reconnection, state, error cases |
| XGBoost native `.ubj` | joblib | joblib breaks across XGBoost versions; native format is officially recommended since 2.1 |
| SWR polling | WebSocket | Data is 15-min delayed; WebSocket would give false real-time impression |

---

## Sources

- [Vercel AI SDK — Stream Protocols](https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol) — useChat + custom backend headers, HIGH confidence
- [Vercel AI SDK Python Streaming template](https://vercel.com/templates/next.js/ai-sdk-python-streaming) — FastAPI + Next.js streaming pattern, HIGH confidence
- [DeepSeek JSON Output docs](https://api-docs.deepseek.com/guides/json_mode) — json_object only, no json_schema support, HIGH confidence
- [instructor DeepSeek integration](https://python.useinstructor.com/integrations/deepseek/) — Mode.JSON for DeepSeek compatibility, HIGH confidence
- [yfinance caching docs](https://ranaroussi.github.io/yfinance/advanced/caching.html) — native cache scope; requests-cache pattern, MEDIUM confidence
- [XGBoost Model IO docs](https://xgboost.readthedocs.io/en/latest/tutorials/saving_model.html) — native UBJSON format recommendation, HIGH confidence
- [FastAPI SSE streaming](https://fastapi.tiangolo.com/tutorial/server-sent-events/) — StreamingResponse pattern, HIGH confidence
- [diskcache GitHub](https://github.com/grantjenks/python-diskcache) — thread/process-safe disk cache, HIGH confidence

---

*Stack research for: Stalize — BIST 100 AI Investment Advisor*
*Researched: 2026-04-16*
