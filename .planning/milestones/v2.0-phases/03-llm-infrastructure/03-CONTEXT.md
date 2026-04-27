# Phase 3: LLM Infrastructure - Context

**Gathered:** 2026-04-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Harden all DeepSeek calls so they return structured, validated output (via instructor + Pydantic), are bounded by rate limits (asyncio.Semaphore(5)), and carry staleness warnings when data is older than 15 minutes. No new features, no UI changes.

Requirements in scope: LLMI-01, LLMI-02, LLMI-03.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion

Infrastructure-only phase — all implementation choices at Claude's discretion within the library constraints from requirements.

Key constraints from REQUIREMENTS.md (already decided):
- LLMI-01: `instructor` library integrated; `StockAnalysis` Pydantic model defined with fields: `karar` (AL/SAT/TUT), `risk`, `ödül`, `çelişkiler`, `gerekçe`. DeepSeek has a limitation with json_schema mode — use `instructor.from_openai(client, mode=instructor.Mode.JSON)` (JSON mode, not json_schema).
- LLMI-02: `asyncio.Semaphore(5)` wraps all DeepSeek calls; no more than 5 concurrent calls at any moment. A daily token cap is optional (no hard requirement for exact cap value).
- LLMI-03: Every LLM prompt assembly must include an `as_of` timestamp. If data is older than 15 minutes, the response carries a `staleness_warning` field — never presented as current data.

Implementation notes:
- instructor integration: install `instructor` package; use `instructor.from_openai(client, mode=instructor.Mode.JSON)`
- StockAnalysis model: `karar: Literal["AL", "SAT", "TUT"]`, `risk: str`, `ödül: str`, `çelişkiler: List[str]`, `gerekçe: str`
- Semaphore: module-level `_llm_semaphore = asyncio.Semaphore(5)` in llm_sentiment.py; wrap API calls with `async with _llm_semaphore:`
- Staleness check: compute age of `as_of` at prompt assembly time; if `(datetime.now(timezone.utc) - as_of) > timedelta(minutes=15)` → set `staleness_warning` in response
- The diskcache wrapper from Phase 2 (02-04) wraps `analyze()` — Phase 3 changes go INSIDE `analyze()`, cache is unaffected

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/services/llm_sentiment.py` — `DeepSeekSentimentService` with `AsyncOpenAI` client and existing diskcache wrapper (Phase 2). Modify this file for all 3 requirements.
- `backend/app/core/config.py` — `Settings` class with `DEEPSEEK_API_KEY`, `LLM_MODEL`. Add `LLM_MAX_CONCURRENT: int = 5` here if needed.

### Established Patterns
- Phase 2 added `_llm_cache` module-level singleton — same pattern for `_llm_semaphore`
- `AsyncOpenAI` client already established; instructor wraps it: `instructor.from_openai(client, mode=instructor.Mode.JSON)`

### Integration Points
- `analyze()` method in `DeepSeekSentimentService` — target for all 3 changes (instructor output, semaphore, staleness)
- Return type changes from `Dict` → `StockAnalysis` Pydantic model; callers in router files will need to handle the new return type (use `.dict()` or `.model_dump()` for JSON serialization)

</code_context>

<specifics>
## Specific Ideas

- DeepSeek does NOT support `json_schema` response format — use `instructor.Mode.JSON` not `instructor.Mode.JSON_SCHEMA`
- `StockAnalysis` fields use Turkish names to match the existing prompt/response format
- Staleness warning can be a simple boolean field or a string — "Veri 15 dakikadan eski" style message

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-llm-infrastructure*
*Context gathered: 2026-04-17 (infrastructure phase — auto-generated)*
