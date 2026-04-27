# Phase 3: LLM Infrastructure - Research

**Researched:** 2026-04-17
**Domain:** instructor + Pydantic structured output, asyncio concurrency control, staleness detection
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- LLMI-01: `instructor` library integrated; `StockAnalysis` Pydantic model with fields `karar` (Literal["AL","SAT","TUT"]), `risk: str`, `ödül: str`, `çelişkiler: List[str]`, `gerekçe: str`. Use `instructor.from_openai(client, mode=instructor.Mode.JSON)` — DeepSeek does NOT support json_schema mode.
- LLMI-02: `asyncio.Semaphore(5)` module-level in llm_sentiment.py wraps all DeepSeek calls. No more than 5 concurrent calls at any time.
- LLMI-03: Every LLM prompt must include `as_of` timestamp. If data age > 15 minutes → set `staleness_warning` field in response.
- Target file: `backend/app/services/llm_sentiment.py` — modify `DeepSeekSentimentService.analyze()`
- Same module-level singleton pattern as `_llm_cache`: `_llm_semaphore = asyncio.Semaphore(5)`
- instructor wraps existing AsyncOpenAI client: `instructor.from_openai(client, mode=instructor.Mode.JSON)`
- Return type: `Dict` → `StockAnalysis`; callers use `.model_dump()` for JSON serialization
- Phase 3 changes go INSIDE `analyze()`; diskcache wrapper from Phase 2 is unaffected

### Claude's Discretion
- Infrastructure-only phase — all implementation choices at Claude's discretion within the library constraints above
- Staleness warning form: boolean field or string message ("Veri 15 dakikadan eski")

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| LLMI-01 | instructor integrated; StockAnalysis Pydantic model; Mode.JSON | instructor 1.15.1, from_openai(AsyncOpenAI, mode=Mode.JSON), Pydantic 2 BaseModel with Turkish fields |
| LLMI-02 | asyncio.Semaphore(5) module-level, wraps all DeepSeek calls | asyncio.Semaphore pattern, module-level singleton, async with context manager |
| LLMI-03 | as_of timestamp in every prompt; staleness_warning if data > 15 min old | datetime.now(timezone.utc), timedelta(minutes=15), Optional[str] field on StockAnalysis |
</phase_requirements>

---

## Summary

Phase 3 hardens the existing `DeepSeekSentimentService.analyze()` in `llm_sentiment.py` along three axes: structured output validation (instructor + Pydantic), concurrency limiting (asyncio.Semaphore), and data freshness signalling (staleness_warning). No new routes or UI changes are involved.

The instructor library (v1.15.1, current as of April 2026) fully supports Python 3.9 (`requires-python = ">=3.9"`) and wraps `AsyncOpenAI` via `instructor.from_openai(async_client, mode=instructor.Mode.JSON)`. After patching, the async path calls `await patched_client.chat.completions.create(..., response_model=StockAnalysis)` and returns a validated `StockAnalysis` instance rather than a raw dict. DeepSeek does not support `Mode.JSON_SCHEMA` (OpenAI structured-output format) — `Mode.JSON` (plain JSON mode) is confirmed compatible.

The primary migration risk is callers: four service files (`sentiment.py`, `kap_parser.py`, `tuik_adapter.py`, `tcmb_adapter.py`) access `analyze()` return values via dict-key syntax (`analysis["sentiment_score"]`, `analysis.get("sentiment_score")`). These fields do not exist on the new `StockAnalysis` model. The transition strategy is a **compatibility shim**: `analyze()` returns `StockAnalysis` but a thin wrapper in each caller calls `.model_dump()` to get a dict, OR — since all four call-sites only consume `sentiment_score`, `sentiment_label`, `sentiment_confidence`, `importance_score` — those four fields are added to `StockAnalysis` as computed properties so the model is directly subscript-compatible after patching callers to use `.model_dump()`.

**Primary recommendation:** Add `instructor` to `requirements.txt`, define `StockAnalysis` at module level in `llm_sentiment.py`, patch `DeepSeekSentimentService.__init__` to create a patched async client, add `_llm_semaphore` module-level, update `analyze()` signature to accept `as_of: Optional[datetime] = None`, and update all four calling services to call `.model_dump()` on the returned object before accessing legacy fields.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| instructor | 1.15.1 | Wraps LLM clients to enforce Pydantic-validated structured output | Official integration with OpenAI-compatible APIs; supports Mode.JSON for DeepSeek |
| pydantic | 2.11.1 (already installed) | Model definition and validation | Already in requirements; instructor 1.x requires pydantic >=2 |
| asyncio (stdlib) | 3.9 stdlib | Semaphore for concurrency control | No extra package needed; asyncio.Semaphore is stdlib |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| openai (AsyncOpenAI) | already installed | Async HTTP client to DeepSeek | Already present; instructor wraps it |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| instructor Mode.JSON | instructor Mode.MD_JSON | MD_JSON is better for reasoning models (deepseek-reasoner), JSON is correct for deepseek-chat; requirement mandates JSON |
| asyncio.Semaphore | aiohttp TCPConnector limit | Semaphore is simpler and already in stdlib; requirement mandates Semaphore |

**Installation (add to requirements.txt):**
```bash
instructor==1.15.1
```

**Version verification (confirmed 2026-04-17):**
```bash
pip index versions instructor  # Latest: 1.15.1
```

---

## Architecture Patterns

### Recommended Module Structure (llm_sentiment.py)

```
Module level (top of file)
├── _llm_cache = diskcache.Cache(...)        ← Phase 2, unchanged
├── _llm_semaphore = asyncio.Semaphore(5)    ← Phase 3 LLMI-02
├── class StockAnalysis(BaseModel)           ← Phase 3 LLMI-01
└── class DeepSeekSentimentService
    ├── __init__: creates AsyncOpenAI client AND instructor-patched client
    └── analyze(title, summary, source, symbol, event_type, as_of) → StockAnalysis
```

### Pattern 1: instructor.from_openai with AsyncOpenAI and Mode.JSON

**What:** Wraps an existing `AsyncOpenAI` instance so `.chat.completions.create()` accepts `response_model=` and returns a validated Pydantic object instead of raw text.
**When to use:** Any OpenAI-compatible endpoint that supports JSON mode but NOT structured output (OpenAI's json_schema format). DeepSeek is exactly this case.

```python
# Source: https://python.useinstructor.com/concepts/patching/
import instructor
from openai import AsyncOpenAI

raw_client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com/v1"
)
patched_client = instructor.from_openai(raw_client, mode=instructor.Mode.JSON)

# async usage — returns StockAnalysis directly, raises ValidationError on bad output
result: StockAnalysis = await patched_client.chat.completions.create(
    model=model,
    messages=[...],
    response_model=StockAnalysis,
    temperature=0.2,
    max_tokens=500,
)
```

**Key detail:** `from_openai` detects `AsyncOpenAI` and returns an `AsyncInstructor` instance. The `.chat.completions.create()` method on `AsyncInstructor` is awaitable. No `apatch` needed in v1.x.

### Pattern 2: asyncio.Semaphore for concurrency limiting

**What:** Module-level `asyncio.Semaphore(5)` limits simultaneous DeepSeek calls.
**When to use:** Any async service that must cap concurrent external API calls.

```python
# Source: Python 3.9 stdlib asyncio docs
import asyncio

_llm_semaphore = asyncio.Semaphore(5)  # module-level singleton

async def analyze(self, ...):
    ...
    async with _llm_semaphore:
        result = await self._patched_client.chat.completions.create(
            ...,
            response_model=StockAnalysis,
        )
    return result
```

**CRITICAL placement:** The `async with _llm_semaphore:` block MUST wrap only the live API call, NOT the cache check. The cache read happens before acquiring the semaphore so cache hits do not occupy a semaphore slot.

### Pattern 3: StockAnalysis Pydantic model with Turkish fields

**What:** Pydantic v2 BaseModel with Unicode field names and `Optional[str]` for staleness_warning.
**When to use:** Structured return type for all LLM analysis results.

```python
# Source: Pydantic v2 docs, instructor requirement LLMI-01
from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class StockAnalysis(BaseModel):
    karar: Literal["AL", "SAT", "TUT"]
    risk: str
    ödül: str
    çelişkiler: List[str]
    gerekçe: str
    staleness_warning: Optional[str] = None  # LLMI-03: set if as_of > 15 min old
```

**Python 3.9 note:** `list[str]` lowercase generics work only in 3.9+ but `List[str]` from `typing` is safe and explicit. Use `Optional[str]` from `typing`, not `str | None` (3.10+ syntax). The `Literal` type is available from `typing` in 3.8+.

### Pattern 4: Staleness detection

**What:** Compute age of `as_of` at the top of `analyze()`. Inject warning string into `StockAnalysis` if age > 15 minutes.
**When to use:** Every `analyze()` call that receives an `as_of` parameter.

```python
from datetime import datetime, timezone, timedelta

STALENESS_THRESHOLD = timedelta(minutes=15)

async def analyze(self, ..., as_of: Optional[datetime] = None) -> StockAnalysis:
    now = datetime.now(timezone.utc)
    staleness_warning = None
    if as_of is not None:
        # Normalize as_of to UTC if naive
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=timezone.utc)
        age = now - as_of
        if age > STALENESS_THRESHOLD:
            staleness_warning = f"Veri {int(age.total_seconds() // 60)} dakikadan eski"

    # Include as_of in prompt
    as_of_str = (as_of or now).strftime("%Y-%m-%d %H:%M UTC")
    prompt = f"VERİ TARİHİ: {as_of_str}\nKAYNAK: {source}\n..."

    # ... (cache check, semaphore, API call)

    # After getting result from instructor, inject staleness_warning
    result.staleness_warning = staleness_warning
    return result
```

**Key detail:** instructor constructs the Pydantic object from LLM output. `staleness_warning` must default to `None` in the model so instructor never tries to have the LLM generate it — the field is set AFTER instructor returns.

### Pattern 5: Caller migration — dict → model_dump()

**What:** Four callers access analyze() results by dict key. After return type becomes `StockAnalysis`, they must call `.model_dump()` or access attributes directly.
**When to use:** Any call-site that does `analysis["key"]` or `analysis.get("key")`.

```python
# Before (4 files: sentiment.py, kap_parser.py, tuik_adapter.py, tcmb_adapter.py)
analysis = await llm_sentiment_service.analyze(...)
score = analysis["sentiment_score"]          # KeyError after migration

# After option A — model_dump() shim
analysis = (await llm_sentiment_service.analyze(...)).model_dump()
score = analysis.get("sentiment_score", 0.0)  # works as before

# After option B — add compatibility fields to StockAnalysis (NOT recommended)
# Keeps callers unchanged but pollutes the model with legacy fields
```

**Recommendation:** Option A (`.model_dump()`) is clean and explicit. `model_dump()` is the Pydantic v2 name (`.dict()` is deprecated in v2 but still works as alias). Use `model_dump()`.

### Anti-Patterns to Avoid

- **Do NOT use `Mode.JSON_SCHEMA`:** DeepSeek does not support the OpenAI structured-output (json_schema) response format. The API will return an error. `Mode.JSON` tells instructor to use plain JSON mode.
- **Do NOT construct a second `AsyncOpenAI` client:** Keep the existing `self.client` as the raw client (for any raw calls); create `self._patched_client = instructor.from_openai(self.client, mode=instructor.Mode.JSON)` as the instructor-wrapped reference to the SAME client.
- **Do NOT place semaphore around cache read:** Cache lookups are CPU-only and should not consume a semaphore slot.
- **Do NOT use `str | None` union syntax:** Python 3.9 requires `Optional[str]` from `typing` for type unions in Pydantic field definitions.
- **Do NOT instruct the model to set `staleness_warning`:** That field must be excluded from the prompt/system instructions. The LLM should only generate the 5 business-logic fields; staleness is set programmatically post-response.
- **Do NOT pass naive datetimes without UTC normalization:** `datetime.utcnow()` is deprecated in 3.12+ and returns naive objects. Always use `datetime.now(timezone.utc)`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Validated structured LLM output | Custom JSON parse + manual Pydantic construction | `instructor` + `response_model=` | instructor handles retry on ValidationError, JSON extraction from markdown fences, and type coercion automatically |
| Concurrency limiting | Manual counter + asyncio.Event | `asyncio.Semaphore` | Semaphore is atomic, handles cancellation, zero dependencies |
| JSON extraction from markdown | Regex strip of ``` fences (already in code lines 98-102) | instructor | instructor's Mode.JSON already strips fences and retries — the manual regex in the current code becomes redundant |

**Key insight:** The existing `json.loads` + manual JSON cleanup (lines 95–103 of current code) is replaced entirely by instructor. If DeepSeek returns markdown-wrapped JSON, instructor's Mode.JSON handles extraction automatically.

---

## Caller Impact Map

All callers of `llm_sentiment_service.analyze()` and the specific dict keys they access:

| File | Line range | Keys accessed | Migration action |
|------|------------|--------------|-----------------|
| `sentiment.py` | 56–57 | `["sentiment_score"]`, `["importance_score"]` | Add `.model_dump()` after `await` |
| `kap_parser.py` | 151–154 | `["sentiment_score"]`, `["sentiment_label"]`, `["sentiment_confidence"]`, `["importance_score"]` | Add `.model_dump()` after `await` |
| `tuik_adapter.py` | 385–387 | `.get("sentiment_score")`, `.get("sentiment_label")`, `.get("sentiment_confidence")` | Add `.model_dump()` after `await` |
| `tcmb_adapter.py` | 337–339 | `.get("sentiment_score")`, `.get("sentiment_label")`, `.get("sentiment_confidence")` | Add `.model_dump()` after `await` |
| `event_fusion.py` | imports only | None — imported but no `.analyze()` call found | No change needed |

**IMPORTANT:** `StockAnalysis` fields (`karar`, `risk`, `ödül`, `çelişkiler`, `gerekçe`, `staleness_warning`) do NOT include `sentiment_score`, `sentiment_label`, `sentiment_confidence`, or `importance_score`. These four legacy fields exist only for the callers listed above. After migration each caller will use `.model_dump()` to get a dict — then access the legacy fields — which means `StockAnalysis.model_dump()` will NOT contain `sentiment_score` etc.

**Resolution:** The `analyze()` method must still build and return the legacy dict for these callers, OR callers must be updated to derive equivalent values from `StockAnalysis.karar`/`StockAnalysis.gerekçe`. The cleanest approach is:

1. `analyze()` returns `StockAnalysis` (pure new model).
2. Each caller converts: `result = await llm_sentiment_service.analyze(...); analysis = _to_legacy(result)` where `_to_legacy` is a small helper that derives `sentiment_score` from `karar` (AL→+0.7, TUT→0.0, SAT→-0.7), `sentiment_label` from `karar`, `sentiment_confidence=0.9`, `importance_score` from abs of derived score.
3. This keeps callers working without polluting `StockAnalysis`.

Alternatively: add a `to_legacy_dict()` method on `StockAnalysis` itself. Either way, the mapping must be explicit, not silent.

---

## Common Pitfalls

### Pitfall 1: Mode.JSON_SCHEMA with DeepSeek
**What goes wrong:** `instructor.from_openai(client, mode=instructor.Mode.JSON_SCHEMA)` causes a 400 error from DeepSeek — "Unsupported response_format type."
**Why it happens:** DeepSeek's API is OpenAI-compatible only for basic chat and JSON mode; the structured output (json_schema) format is an OpenAI-proprietary extension.
**How to avoid:** Always use `mode=instructor.Mode.JSON` for DeepSeek.
**Warning signs:** 400 error on first API call after patching.

### Pitfall 2: asyncio.Semaphore created outside event loop (Python 3.9)
**What goes wrong:** `_llm_semaphore = asyncio.Semaphore(5)` at module import time raises `DeprecationWarning` in Python 3.10+ and silently attaches to the wrong loop in 3.9 if the loop was not yet running at import time.
**Why it happens:** In Python 3.9, `asyncio.Semaphore()` uses the running loop at creation time. Module-level creation happens before FastAPI/uvicorn starts the event loop.
**How to avoid:** In Python 3.9 specifically, module-level `asyncio.Semaphore(5)` is safe IF the module is imported lazily (i.e., after uvicorn starts the loop). Since `llm_sentiment.py` is imported by service files which are imported by router files which are imported at app startup, the timing is correct. However, to be explicit: if tests fail with "no current event loop," use `asyncio.get_event_loop().run_until_complete(...)` in test setup or switch to `asyncio.Semaphore(5)` created inside a lazy `__init__` if issues arise. The Phase 2 `_llm_cache` used module-level initialization without issues, so the same pattern applies.
**Warning signs:** `RuntimeError: no running event loop` during tests.

### Pitfall 3: instructor ValidationError on bad LLM output kills the cache miss path
**What goes wrong:** If DeepSeek returns malformed JSON or a missing field, instructor raises `pydantic.ValidationError` (or `instructor.exceptions.InstructorRetryException` after max_retries). The current code catches `json.JSONDecodeError` and returns a fallback dict — this catch must be updated to also catch `ValidationError`.
**Why it happens:** instructor raises `ValidationError` (not `JSONDecodeError`) when the model fails to produce a conforming response after retries.
**How to avoid:** Add `except ValidationError` (and optionally `except instructor.exceptions.InstructorRetryException`) to the `try/except` block, returning a fallback `StockAnalysis` with `karar="TUT"` and empty fields.
**Warning signs:** Uncaught `pydantic.ValidationError` exceptions in logs.

### Pitfall 4: Pydantic v2 `.dict()` vs `.model_dump()`
**What goes wrong:** Callers that use `analysis.dict()` after migration get a `PydanticUserError` in strict mode or a deprecation warning.
**Why it happens:** Pydantic v2 renamed `.dict()` to `.model_dump()`. `.dict()` still works as an alias but will be removed in a future version.
**How to avoid:** Use `.model_dump()` explicitly in all four caller migration sites.

### Pitfall 5: Staleness warning leaks into LLM prompt as a required field
**What goes wrong:** If the system prompt lists `staleness_warning` as a field the model must produce, the model will hallucinate content for it. This field is not a business-logic output from the LLM.
**Why it happens:** instructor informs the model of the Pydantic schema. If `staleness_warning` has no `default` or `default_factory`, instructor includes it in the schema sent to the model.
**How to avoid:** Define `staleness_warning: Optional[str] = None` with an explicit default. instructor will mark it as optional in the schema and the model is free to omit it. Then set it programmatically after the instructor call returns.

### Pitfall 6: Turkish Unicode field names in Pydantic
**What goes wrong:** `ödül` and `çelişkiler` use non-ASCII characters. Python 3.9 allows Unicode identifiers natively, but JSON serialization via `.model_dump()` preserves them as-is, which may cause issues with downstream JSON parsers that expect ASCII keys.
**Why it happens:** Pydantic v2 uses the Python attribute name as the JSON key by default.
**How to avoid:** Fields work fine in Python 3.9+. If downstream JSON consumers expect ASCII, use `Field(alias="odul")` with `model_config = ConfigDict(populate_by_name=True)`. For this phase (no UI changes), the Turkish keys are fine as-is since callers read the legacy compatibility dict, not the raw `StockAnalysis` keys.

---

## Code Examples

### Complete StockAnalysis model

```python
# Source: instructor docs + Pydantic v2 docs + LLMI-01 requirement
from pydantic import BaseModel
from typing import List, Literal, Optional

class StockAnalysis(BaseModel):
    karar: Literal["AL", "SAT", "TUT"]
    risk: str
    ödül: str
    çelişkiler: List[str]
    gerekçe: str
    staleness_warning: Optional[str] = None  # set programmatically, never by LLM
```

### Module-level declarations

```python
import asyncio
import instructor

_llm_semaphore = asyncio.Semaphore(5)   # LLMI-02 — same pattern as _llm_cache
```

### Patched client initialization (inside __init__)

```python
# Source: instructor v1.x docs
if self.api_key:
    self.client = AsyncOpenAI(
        api_key=self.api_key,
        base_url="https://api.deepseek.com/v1"
    )
    self._patched_client = instructor.from_openai(
        self.client,
        mode=instructor.Mode.JSON  # NOT Mode.JSON_SCHEMA — DeepSeek incompatible
    )
    settings.LLM_ENABLED = True
```

### analyze() skeleton with all three requirements

```python
from datetime import datetime, timezone, timedelta

_STALENESS_THRESHOLD = timedelta(minutes=15)

async def analyze(
    self,
    title: str,
    summary: str = "",
    source: str = "Unknown",
    symbol: str = None,
    event_type: str = None,
    as_of: Optional[datetime] = None,   # LLMI-03
) -> StockAnalysis:

    if not self.client:
        return StockAnalysis(
            karar="TUT", risk="", ödül="", çelişkiler=[], gerekçe="LLM devre dışı"
        )

    # ── Cache check (before semaphore — cache hits don't need a slot) ──────────
    date_str = date.today().isoformat()
    cache_key = f"analysis:{symbol}:{date_str}:{hash(title)}"
    cached = _llm_cache.get(cache_key)
    if cached is not None:
        return cached  # returns StockAnalysis (Phase 3 cache stores models, not dicts)

    # ── Staleness detection (LLMI-03) ──────────────────────────────────────────
    now = datetime.now(timezone.utc)
    staleness_warning = None
    if as_of is not None:
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=timezone.utc)
        age = now - as_of
        if age > _STALENESS_THRESHOLD:
            staleness_warning = (
                f"Veri {int(age.total_seconds() // 60)} dakikadan eski"
            )

    as_of_str = (as_of or now).strftime("%Y-%m-%d %H:%M UTC")
    prompt = (
        f"VERİ TARİHİ: {as_of_str}\n"
        f"KAYNAK: {source}\n"
        f"HABER BAŞLIĞI: {title}\n"
        f"İÇERİK: {summary}\n\n"
        "Bu haberin detaylı etkisini analiz et ve JSON ver:"
    )

    try:
        # ── Concurrency limit (LLMI-02) ────────────────────────────────────────
        async with _llm_semaphore:
            result: StockAnalysis = await self._patched_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                response_model=StockAnalysis,
                temperature=0.2,
                max_tokens=500,
            )

        result.staleness_warning = staleness_warning   # LLMI-03 post-injection
        _llm_cache.set(cache_key, result, expire=1800)
        return result

    except Exception as e:
        logger.error(f"DeepSeek/instructor hatası: {e}")
        return StockAnalysis(
            karar="TUT", risk="", ödül="", çelişkiler=[], gerekçe="Hata"
        )
```

### Legacy compatibility helper (for callers)

```python
def _stock_analysis_to_legacy(analysis: StockAnalysis) -> dict:
    """Map StockAnalysis → legacy dict consumed by kap_parser, sentiment, tuik, tcmb."""
    score_map = {"AL": 0.7, "TUT": 0.0, "SAT": -0.7}
    label_map = {"AL": "pozitif", "TUT": "nötr", "SAT": "negatif"}
    score = score_map.get(analysis.karar, 0.0)
    return {
        "sentiment_score": score,
        "sentiment_label": label_map.get(analysis.karar, "nötr"),
        "sentiment_confidence": 0.9,
        "importance_score": abs(score) * 10,
        "summary": analysis.gerekçe[:100] if analysis.gerekçe else "",
        "reasoning": analysis.gerekçe,
        "staleness_warning": analysis.staleness_warning,
    }
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual `json.loads` + regex fence stripping | instructor `response_model=` | instructor v0.3+ | Eliminates 30 lines of parse/fallback boilerplate |
| `instructor.patch(AsyncOpenAI())` | `instructor.from_openai(client, mode=...)` | instructor v1.0.0 (Apr 2024) | `patch` still works as alias but deprecated |
| `from_openai` returns dict | Returns typed Pydantic object | instructor v1.0 | IDE type inference, automatic retry on ValidationError |

**Deprecated/outdated:**
- `instructor.patch()`: replaced by `instructor.from_openai()` in v1.0.0. Still works but is not documented in current instructor docs.
- `.dict()` on Pydantic v2 models: use `.model_dump()` instead.
- `datetime.utcnow()`: deprecated in Python 3.12; use `datetime.now(timezone.utc)`.

---

## Open Questions

1. **Cache stores dict or StockAnalysis?**
   - What we know: Phase 2 cache stores plain `dict` values; diskcache uses pickle.
   - What's unclear: diskcache pickles `StockAnalysis` fine, but the existing tests for cache (test_llm_cache.py) mock a `dict` return, so they will break if cache stores `StockAnalysis`.
   - Recommendation: Store `StockAnalysis` objects (picklable). Update `test_llm_cache.py` mock to return a `StockAnalysis` or to call `make_mock_response` that produces an instructor-compatible structure.

2. **`_patched_client` on `self` vs module-level**
   - What we know: `_llm_semaphore` and `_llm_cache` are module-level; `self.client` is instance-level.
   - What's unclear: If `DeepSeekSentimentService()` is instantiated multiple times (tests do this via `__new__`), each instance needs its own patched client.
   - Recommendation: Keep `self._patched_client` on `self` (initialized in `__init__`), matching where `self.client` lives.

3. **system prompt update for StockAnalysis fields**
   - What we know: Current system prompt describes a different schema (`impact_score`, `direction`, etc.). instructor uses the Pydantic model schema to guide the LLM.
   - What's unclear: Whether DeepSeek follows the instructor-injected schema without an explicit field list in the system prompt.
   - Recommendation: Update `_build_system_prompt()` to describe the new StockAnalysis fields (`karar`, `risk`, `ödül`, `çelişkiler`, `gerekçe`) so the model understands what to produce. instructor injects the JSON schema but a human-readable description in the system prompt improves reliability.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | `backend/pytest.ini` (asyncio_mode = auto) |
| Quick run command | `cd backend && python -m pytest tests/test_llm_infrastructure.py -x -q` |
| Full suite command | `cd backend && python -m pytest tests/ -x -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LLMI-01 | analyze() returns StockAnalysis instance (not dict) | unit | `pytest tests/test_llm_infrastructure.py::test_returns_stock_analysis -x` | Wave 0 |
| LLMI-01 | StockAnalysis.karar is one of AL/SAT/TUT | unit | `pytest tests/test_llm_infrastructure.py::test_karar_valid_values -x` | Wave 0 |
| LLMI-01 | instructor ValidationError on bad LLM output returns fallback | unit | `pytest tests/test_llm_infrastructure.py::test_validation_error_fallback -x` | Wave 0 |
| LLMI-02 | Semaphore limits to 5 concurrent calls | unit | `pytest tests/test_llm_infrastructure.py::test_semaphore_limits_concurrency -x` | Wave 0 |
| LLMI-03 | staleness_warning is None when as_of < 15 min | unit | `pytest tests/test_llm_infrastructure.py::test_no_staleness_warning -x` | Wave 0 |
| LLMI-03 | staleness_warning is set when as_of > 15 min | unit | `pytest tests/test_llm_infrastructure.py::test_staleness_warning_set -x` | Wave 0 |
| LLMI-03 | as_of timestamp present in prompt | unit | `pytest tests/test_llm_infrastructure.py::test_as_of_in_prompt -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd backend && python -m pytest tests/test_llm_infrastructure.py -x -q`
- **Per wave merge:** `cd backend && python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_llm_infrastructure.py` — covers all LLMI-01/02/03 requirements
- [ ] Update `backend/tests/test_llm_cache.py` — mock must return `StockAnalysis` not raw dict after migration
- [ ] `instructor==1.15.1` added to `backend/requirements.txt` before tests run

---

## Sources

### Primary (HIGH confidence)
- PyPI `pip index versions instructor` — confirmed latest version 1.15.1 (checked 2026-04-17)
- https://github.com/jxnl/instructor/blob/main/pyproject.toml — Python `requires-python = ">=3.9"` confirmed
- https://python.useinstructor.com/blog/2024/04/01/announce-instructor-v1/ — `from_openai` replaces `patch` in v1.0
- https://python.useinstructor.com/integrations/deepseek/ — Mode.JSON and async_client confirmed for DeepSeek
- Python 3.9 stdlib `asyncio.Semaphore` — stdlib, no version caveat

### Secondary (MEDIUM confidence)
- https://python.useinstructor.com/concepts/patching/ — Mode.JSON described; async patching pattern confirmed
- https://python.useinstructor.com/integrations/openai/ — `from_openai(async_client, ...)` returns awaitable `AsyncInstructor`
- WebSearch result: "Structured Output fail with Claude Sonnet and DeepSeek providers" (openai-agents-python issue #2032, Nov 2025) — confirms DeepSeek structured-output (JSON_SCHEMA) problems; JSON mode works

### Tertiary (LOW confidence)
- WebSearch result: `instructor.apatch` is the old async pattern pre-v1.0; v1.x `from_openai` detects async automatically — single source (blog post), not verified against current source code directly

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — version confirmed via PyPI, Python 3.9 compat confirmed via pyproject.toml
- Architecture: HIGH — instructor and asyncio patterns verified against official docs; caller migration verified via source code inspection
- Pitfalls: HIGH for Mode.JSON_SCHEMA/DeepSeek (multiple sources); MEDIUM for asyncio.Semaphore event loop timing (known Python 3.9 behavior, not tested in this project)
- Caller impact map: HIGH — derived from direct source code grep of all 4 call sites

**Research date:** 2026-04-17
**Valid until:** 2026-05-17 (instructor moves fast; re-verify if upgrading past 1.15.x)
