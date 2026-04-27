# Architecture Research

**Domain:** BIST 100 AI Investment Advisor — Brownfield AI Chat + Briefing Integration
**Researched:** 2026-04-16
**Confidence:** HIGH (based on direct codebase analysis + verified FastAPI streaming patterns)

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        NEXT.JS FRONTEND (port 3000)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │  Dashboard   │  │  Chat Page   │  │  Other Pages │               │
│  │ (Briefing)   │  │ (AI Chat)    │  │  (unchanged) │               │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘               │
│         │                 │ SSE (text/event-stream)                  │
│         │ REST            │ + REST                                   │
└─────────┼─────────────────┼────────────────────────────────────────-┘
          │                 │
┌─────────┼─────────────────┼─────────────────────────────────────────┐
│         ▼                 ▼                                          │
│         FASTAPI API LAYER (port 8000)                                │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │ api/endpoints.py (existing routes, unchanged)                │    │
│  │ api/chat.py (NEW — /api/chat/stream, /api/chat/history)      │    │
│  │ api/briefing.py (NEW — /api/briefing/today, /api/briefing/)  │    │
│  └───────┬────────────────────────────┬─────────────────────────┘    │
│          │                            │                              │
│  ┌───────▼──────────┐    ┌────────────▼────────────┐                │
│  │  ChatService     │    │  BriefingService         │                │
│  │  (NEW)           │    │  (NEW)                   │                │
│  │  - build_context │    │  - generate_briefing()   │                │
│  │  - stream_reply  │    │  - fetch_today_briefing  │                │
│  └───────┬──────────┘    └────────────┬────────────┘                │
│          │                            │                              │
│  ┌───────▼────────────────────────────▼────────────┐                │
│  │           DeepSeekLLMClient (SHARED)             │                │
│  │  Thin wrapper around existing AsyncOpenAI        │                │
│  │  client — streaming=True for chat,               │                │
│  │  streaming=False for briefing generation         │                │
│  └───────┬─────────────────────────────────────────┘                │
│          │                                                           │
│  EXISTING SERVICES (READ-ONLY from new components)                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ scoring  │ │technical │ │ kap_     │ │ causal   │ │ market_  │  │
│  │ _engine  │ │ _engine  │ │ parser   │ │ _engine  │ │intellig. │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│                                                                      │
│  APSCHEDULER (existing + one new job)                                │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ background_briefing_generation (NEW — cron weekdays 06:30)    │  │
│  │ + all existing jobs unchanged                                  │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
          │
┌─────────▼────────────────────────────────────────────────────────────┐
│                         POSTGRESQL                                    │
│  ┌──────────────┐  ┌───────────────────┐  ┌──────────────────────┐   │
│  │ Stock +      │  │ DailyBriefing     │  │ ChatMessage          │   │
│  │ NewsItem +   │  │ (NEW table)       │  │ (NEW table)          │   │
│  │ MacroIndicator│  │ id, date, content │  │ id, role, content,  │   │
│  │ (existing)   │  │ summary_json,     │  │ timestamp, context_ │   │
│  │              │  │ generated_at      │  │ snapshot_json        │   │
│  └──────────────┘  └───────────────────┘  └──────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
          │
┌─────────▼──────────┐
│  DEEPSEEK API      │
│  (external, HTTPS) │
│  openai SDK compat │
└────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Location |
|-----------|----------------|----------|
| `ChatService` | Build context snapshot, call DeepSeek with streaming, detect stock-query intent, assemble 3-layer analysis | `backend/app/services/chat.py` (NEW) |
| `BriefingService` | Generate daily morning summary using all data sources, persist to DB, serve stored result | `backend/app/services/briefing.py` (NEW) |
| `DeepSeekLLMClient` | Thin async wrapper over existing `AsyncOpenAI` client; streaming and non-streaming modes | Extract from `llm_sentiment.py` or keep inline in new services |
| `api/chat.py` | POST /api/chat/stream (SSE), GET /api/chat/history | `backend/app/api/chat.py` (NEW) |
| `api/briefing.py` | GET /api/briefing/today, GET /api/briefing/ (list) | `backend/app/api/briefing.py` (NEW) |
| `DailyBriefing` ORM model | Store one generated briefing per day; idempotent (upsert on date) | `backend/app/models/briefing.py` (NEW) |
| `ChatMessage` ORM model | Persist conversation history for context window reconstruction | `backend/app/models/chat.py` (NEW) |
| `background_briefing_generation` | APScheduler cron job — runs at 06:30 weekdays, calls BriefingService, stores to DB | `backend/app/main.py` lifespan (NEW job) |
| Existing services | Provide scored data, news, macro context — read-only from new components | `backend/app/services/` (unchanged) |

## Recommended Project Structure

New files follow existing conventions. Zero existing files are moved or renamed.

```
backend/app/
├── api/
│   ├── endpoints.py          # existing — DO NOT TOUCH structure
│   ├── chat.py               # NEW — chat endpoints
│   └── briefing.py           # NEW — briefing endpoints
├── models/
│   ├── briefing.py           # NEW — DailyBriefing ORM model
│   └── chat.py               # NEW — ChatMessage ORM model
├── services/
│   ├── chat.py               # NEW — ChatService singleton
│   └── briefing.py           # NEW — BriefingService singleton
└── main.py                   # existing — add briefing job + mount new routers

frontend/src/
├── app/
│   ├── page.tsx              # existing Dashboard — fetch /api/briefing/today
│   └── chat/
│       └── page.tsx          # NEW — AI chat page (SSE consumer)
├── lib/
│   └── api.ts                # existing — add chat + briefing typed methods
└── components/
    └── ChatMessage.tsx        # NEW — message bubble component
```

### Structure Rationale

- **api/chat.py separate from endpoints.py**: `endpoints.py` is already 38k characters. New chat routes use `StreamingResponse` which has a different response model; keeping it separate avoids router conflicts and makes the streaming behavior explicit.
- **api/briefing.py separate**: Briefing has its own idempotency logic and cron dependency. Isolating it makes that explicit.
- **services/chat.py and services/briefing.py**: Follows existing singleton pattern (`chat_service = ChatService()` at module bottom). New services import from existing services — they don't modify them.
- **models/briefing.py and models/chat.py**: Each new table gets its own file, consistent with `models/stock.py`, `models/news.py` convention. Both re-exported from `models/__init__.py`.

## Architectural Patterns

### Pattern 1: Context Snapshot Assembly (Chat)

**What:** Before calling DeepSeek for a chat reply, `ChatService.build_context()` queries the DB once to assemble a frozen snapshot of current reality — top stock scores, today's KAP headlines, latest macro indicators, and the last N chat messages. This snapshot is serialized and injected into the system prompt.

**When to use:** Every chat turn. The snapshot is cheap (indexed queries), prevents stale LLM responses, and makes every reply grounded in current DB state.

**Trade-offs:** Adds ~50-100ms per request for DB queries; snapshot grows with requested context depth. Keep to last 5 KAP items, top 10 stocks by score, and last 10 chat messages to stay within DeepSeek's context window.

```python
# backend/app/services/chat.py
class ChatService:
    async def build_context(self, db, symbol: str | None = None) -> dict:
        top_stocks = await db.execute(
            select(Stock).order_by(Stock.overall_score.desc()).limit(10)
        )
        recent_kap = await db.execute(
            select(NewsItem).order_by(NewsItem.published_at.desc()).limit(5)
        )
        macro = await db.execute(
            select(MacroIndicator).order_by(MacroIndicator.date.desc()).limit(5)
        )
        # If symbol specified, pull 3-layer data for that stock
        stock_detail = None
        if symbol:
            stock_detail = await self._get_stock_analysis(db, symbol)
        return {"stocks": ..., "kap": ..., "macro": ..., "stock_detail": stock_detail}

    async def stream_reply(self, user_message: str, context: dict, history: list):
        system_prompt = self._build_system_prompt(context)
        messages = [{"role": "system", "content": system_prompt}]
        messages += history  # last N turns from ChatMessage table
        messages.append({"role": "user", "content": user_message})

        async with self.client.chat.completions.stream(
            model=settings.LLM_MODEL,
            messages=messages,
        ) as stream:
            async for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                yield delta
```

### Pattern 2: SSE Streaming via FastAPI StreamingResponse

**What:** The chat endpoint uses `StreamingResponse` with `media_type="text/event-stream"`. The async generator yields SSE-formatted chunks (`data: {token}\n\n`). The frontend uses `EventSource` or `fetch` with `ReadableStream` to consume it.

**When to use:** Any endpoint where the user should see tokens appear progressively — chat replies and optionally structured analysis generation.

**Trade-offs:** SSE is one-directional (server to client) and cannot be cancelled mid-stream without client disconnect detection. Use `asyncio.CancelledError` handling in the generator to clean up if the client disconnects.

```python
# backend/app/api/chat.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/chat")

@router.post("/stream")
async def stream_chat(request: ChatRequest):
    async def generator():
        async with AsyncSessionLocal() as db:
            context = await chat_service.build_context(db, request.symbol)
            history = await chat_service.get_history(db, limit=10)
            full_reply = ""
            async for token in chat_service.stream_reply(request.message, context, history):
                full_reply += token
                yield f"data: {token}\n\n"
            # Persist after stream completes
            await chat_service.save_message(db, "user", request.message, context)
            await chat_service.save_message(db, "assistant", full_reply, {})

    return StreamingResponse(generator(), media_type="text/event-stream")
```

### Pattern 3: Idempotent Scheduled Briefing Generation

**What:** `BriefingService.generate_briefing()` runs at 06:30 on weekdays via APScheduler. It assembles the full morning context (price movements from last close, KAP overnight, macro), calls DeepSeek (non-streaming, full response), and upserts a `DailyBriefing` row keyed on today's date. Dashboard fetches `/api/briefing/today` — returns the stored row immediately, no LLM call at request time.

**When to use:** Any AI-generated content that is expensive to produce but can be pre-computed. Pre-generation means dashboard load time is sub-100ms even though generating the briefing takes 5-15 seconds.

**Trade-offs:** If the cron job fails, the briefing is stale. Mitigate with a fallback endpoint that triggers on-demand generation if today's briefing is absent, with a loading state in the UI.

```python
# backend/app/services/briefing.py
class BriefingService:
    async def generate_briefing(self) -> DailyBriefing:
        async with AsyncSessionLocal() as db:
            today = date.today()
            existing = await db.execute(
                select(DailyBriefing).where(
                    func.date(DailyBriefing.generated_at) == today
                )
            )
            if existing.scalar():
                return  # Already generated today, skip

            context = await self._build_morning_context(db)
            content = await self._call_llm(context)  # Non-streaming

            briefing = DailyBriefing(
                generated_at=datetime.utcnow(),
                content=content,
                summary_json=json.dumps(context["highlights"])
            )
            db.add(briefing)
            await db.commit()
```

### Pattern 4: Structured 3-Layer Analysis Output

**What:** When the user asks about a specific stock in chat, `ChatService` detects the intent (symbol present in message or explicit request body), enriches the context with that stock's technical, fundamental, and sentiment sub-scores, and instructs DeepSeek to return a structured response in a defined JSON envelope within the stream. The frontend renders it as a card.

**When to use:** Stock-specific queries. Generic market questions get plain prose.

**Trade-offs:** Structured output requires DeepSeek to follow JSON schema instructions reliably. Use `temperature=0.1` for structured analysis calls vs `temperature=0.3` for conversational chat. Fall back to plain text if JSON parse fails.

## Data Flow

### Chat Request Flow

```
User types message → Chat Page (Next.js)
    ↓ POST /api/chat/stream  {message, symbol?}
ChatService.build_context(db)
    ↓ queries: Stock (top 10), NewsItem (5 recent), MacroIndicator (5 recent)
    ↓ if symbol: also queries PriceHistory, Fundamental, Stock sub-scores
Context snapshot assembled (dict, not persisted yet)
    ↓
ChatService.get_history(db, limit=10)
    ↓ SELECT from ChatMessage ORDER BY timestamp DESC LIMIT 10
    ↓
DeepSeek API called (stream=True)
    ↓ tokens flow back via AsyncOpenAI streaming
FastAPI StreamingResponse yields SSE chunks
    ↓ text/event-stream
Next.js EventSource / fetch ReadableStream
    ↓ appends tokens to message bubble in real-time
Stream complete → ChatService persists user + assistant messages to ChatMessage
```

### Daily Briefing Flow

```
APScheduler cron 06:30 (weekdays)
    ↓ background_briefing_generation()
BriefingService._build_morning_context(db)
    ↓ queries: Stock (all active, close vs prev_close), NewsItem (overnight),
    ↓          MacroIndicator (latest TCMB/TUIK), CausalChainLog (recent)
Context assembled (price movers, KAP highlights, macro state)
    ↓
DeepSeek API called (stream=False, max_tokens=1500)
    ↓ full response returned
DailyBriefing row upserted (keyed on date)
    ↓

Later: User opens Dashboard
    ↓ GET /api/briefing/today
DB lookup (indexed on generated_at date)
    ↓ < 10ms
JSON response → Dashboard renders briefing card
```

### Score Context Injection Flow

```
Existing pipeline (unchanged):
APScheduler → KAP/TCMB/TUIK → scoring_engine.update_all_scores()
    ↓ writes to Stock.overall_score, .technical_score, .sentiment_score, etc.

New pipeline reads from these columns at chat time:
ChatService.build_context() → SELECT Stock.* ORDER BY overall_score DESC
    ↓ current scores are always in DB — no live re-computation at chat time
```

### Key Data Flows Summary

1. **Briefing pre-generation:** BriefingService reads existing tables → calls LLM once → stores result. Dashboard serves stored result.
2. **Chat context injection:** ChatService queries existing Stock/NewsItem/MacroIndicator tables at message time → injects as LLM system prompt — no score recalculation.
3. **Message persistence:** ChatMessage table stores role + content + context_snapshot_json (the assembled context at time of message). Allows debugging what the LLM saw.
4. **History windowing:** Last 10 messages from ChatMessage are loaded and passed as messages array to DeepSeek. Token cost is bounded.

## New ORM Models

### DailyBriefing

```python
class DailyBriefing(Base):
    __tablename__ = "daily_briefing"
    id = Column(Integer, primary_key=True)
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)
    content = Column(Text)               # Full AI-generated briefing text (markdown)
    summary_json = Column(String)        # JSON: {top_movers, kap_highlights, macro_state}
    generation_duration_s = Column(Float, nullable=True)   # How long LLM took
    __table_args__ = (UniqueConstraint('generated_at::date', name='uq_briefing_date'),)
    # NOTE: Use func.date() in queries; SQLAlchemy handles date truncation
```

### ChatMessage

```python
class ChatMessage(Base):
    __tablename__ = "chat_message"
    id = Column(Integer, primary_key=True)
    role = Column(String(20))            # 'user' | 'assistant' | 'system'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    context_snapshot_json = Column(Text, nullable=True)   # What the LLM saw
    symbol = Column(String(20), nullable=True, index=True) # Stock symbol if stock-specific query
```

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| DeepSeek API | `AsyncOpenAI(base_url="https://api.deepseek.com/v1")` — existing pattern from `llm_sentiment.py`. Reuse client instance. | `stream=True` for chat, `stream=False` for briefing. Same `DEEPSEEK_API_KEY`. |
| yfinance / KAP / TCMB / TUIK | Read-only from PostgreSQL tables already populated by schedulers. New components never call external APIs directly. | This is the correct separation — new AI layer reads from the data layer, never bypasses it. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `ChatService` → existing services | Direct import of singletons (`scoring_engine`, `kap_parser`) for metadata only, but prefer DB reads over calling service methods | Calling service methods may trigger expensive computations. Prefer `SELECT` from already-populated tables. |
| `BriefingService` → existing services | Same — DB reads only | Never call `scoring_engine.update_all_scores()` from briefing — that is the scheduler's job. |
| New API routers → `main.py` | `app.include_router(chat_router, prefix="/api")` + same for briefing router | Mount in lifespan or directly on app after existing router; does not affect existing routes. |
| `ChatMessage` → `DailyBriefing` | No direct relationship — they are independent tables | Chat history is not linked to briefings; briefings are not chat sessions. |

## Anti-Patterns

### Anti-Pattern 1: Re-computing Scores at Chat Time

**What people do:** Call `scoring_engine.calculate_overall_score(stock)` inside the chat endpoint to get "fresh" scores before sending context to LLM.

**Why it's wrong:** `calculate_overall_score` may trigger ML inference, technical indicator computation, or external API calls. A chat endpoint must respond in < 500ms to start the first SSE token. Re-computing kills UX and wastes LLM context budget.

**Do this instead:** Read pre-computed scores directly from `Stock.overall_score`, `Stock.technical_score`, etc. The APScheduler keeps these current. The chat layer trusts the data layer.

### Anti-Pattern 2: Storing Full Conversation in LLM Context Window Without Windowing

**What people do:** Load the entire `chat_message` table history and pass it to every LLM call.

**Why it's wrong:** DeepSeek's context window is bounded. A 6-month conversation history will exceed it, causing silent truncation or errors. Token costs also grow unboundedly.

**Do this instead:** Always limit to the last 10 messages (`LIMIT 10 ORDER BY timestamp DESC`). For stock analysis, use the structured context snapshot rather than referencing old messages about the same stock.

### Anti-Pattern 3: Streaming Briefing Generation at Request Time

**What people do:** When the user opens the dashboard, trigger LLM generation inline and stream the result.

**Why it's wrong:** Briefing generation takes 5-15 seconds. Dashboard load time becomes 5-15 seconds. For a morning routine tool, this is unacceptable.

**Do this instead:** Pre-generate at 06:30 via APScheduler. Dashboard fetches the stored result (< 10ms). If the job failed, show a "Generate now" button that triggers on-demand generation with a loading indicator — not the default path.

### Anti-Pattern 4: Adding Chat Routes to the Existing endpoints.py

**What people do:** Add `@router.post("/chat/stream")` directly into `endpoints.py`.

**Why it's wrong:** `endpoints.py` is already 38k characters. Streaming responses have fundamentally different response headers and error handling than the existing JSON endpoints. Mixing them makes the file harder to reason about and risks header-conflict bugs.

**Do this instead:** Create `api/chat.py` with its own `APIRouter`. Mount it separately in `main.py` alongside the existing router.

### Anti-Pattern 5: Calling DeepSeek Without Temperature Differentiation

**What people do:** Use the same `temperature=0.2` for both conversational chat and structured JSON analysis output.

**Why it's wrong:** `0.2` is fine for sentiment analysis (the current use in `llm_sentiment.py`) but too low for natural-sounding chat, and too high for reliably formatted JSON output.

**Do this instead:** Use `temperature=0.3` for conversational chat replies, `temperature=0.1` for structured 3-layer analysis JSON output, and keep `temperature=0.2` for the existing sentiment analysis calls (unchanged).

## Build Order (Phase Dependencies)

The components have clear dependencies that dictate build order:

**Phase 1 — Foundation (must be first):**
- `models/briefing.py` and `models/chat.py` (DB schema, no dependencies)
- `models/__init__.py` re-exports updated
- Tables are auto-created by existing `Base.metadata.create_all` in lifespan

**Phase 2 — Service Layer (depends on Phase 1):**
- `services/briefing.py` — BriefingService (depends on new DailyBriefing model + existing DB tables)
- `services/chat.py` — ChatService (depends on new ChatMessage model + existing Stock/NewsItem/MacroIndicator models)

**Phase 3 — API Layer (depends on Phase 2):**
- `api/briefing.py` — briefing endpoints (depends on BriefingService)
- `api/chat.py` — chat endpoints with SSE (depends on ChatService)
- Mount new routers in `main.py`

**Phase 4 — Scheduler (depends on Phase 2):**
- Add `background_briefing_generation` job to `main.py` lifespan (depends on BriefingService being importable)

**Phase 5 — Frontend (depends on Phase 3):**
- Update `frontend/src/lib/api.ts` with new typed methods (`getBriefingToday`, `streamChat`)
- Update `frontend/src/app/page.tsx` (Dashboard) to fetch and render briefing
- Create `frontend/src/app/chat/page.tsx` with SSE consumer

Each phase is independently deployable and testable before the next begins. Phases 3 and 4 can run in parallel (they both depend only on Phase 2).

## Scaling Considerations

This is a single-user local tool. Scaling is not a concern. The architecture decisions here are about correctness and maintainability, not throughput.

| Concern | At current scale (1 user, local) |
|---------|----------------------------------|
| LLM latency | Pre-generation for briefing; streaming for chat hides latency perceptually |
| DB connection pool | Existing `AsyncSessionLocal` is sufficient; single writer, low query volume |
| Context window | 10-message history window + bounded context snapshot keeps token count controlled |
| DeepSeek rate limits | Low risk at 1 user; add `asyncio.sleep` backoff on 429 responses in ChatService |

## Sources

- Existing codebase analysis (`backend/app/services/llm_sentiment.py`, `backend/app/main.py`, `backend/app/api/endpoints.py`) — HIGH confidence, direct read
- FastAPI StreamingResponse SSE pattern: [Real-time OpenAI response streaming with FastAPI](https://sevalla.com/blog/real-time-openai-streaming-fastapi/) — MEDIUM confidence
- FastAPI SSE streaming: [How to Stream LLM Responses in Real-Time Using FastAPI and SSE](https://blog.gopenai.com/how-to-stream-llm-responses-in-real-time-using-fastapi-and-sse-d2a5a30f2928) — MEDIUM confidence
- PostgreSQL chat history with async SQLAlchemy: [Building Stateful Conversations with Postgres and LLMs](https://medium.com/@levi_stringer/building-stateful-conversations-with-postgres-and-llms-e6bb2a5ff73e) — MEDIUM confidence
- OpenAI SDK streaming docs: [Streaming API responses](https://developers.openai.com/api/docs/guides/streaming-responses) — HIGH confidence (DeepSeek uses same protocol)

---
*Architecture research for: BIST 100 AI Investment Advisor — AI Chat + Daily Briefing Integration*
*Researched: 2026-04-16*
