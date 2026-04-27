---
phase: 05-ui-redesign
plan_id: 05-01
title: "Backend Macro Endpoint + API Types"
requirements: [UIUX-04, UIUX-01]
wave: 1
estimated_minutes: 40
autonomous: true
depends_on: [05-00]
files_modified:
  - backend/app/api/macro.py
  - frontend/src/lib/api.ts
must_haves:
  truths:
    - "GET /api/macro/indicators returns USD/TRY, gold, BIST100, interest rate, inflation as JSON"
    - "getBriefing() and getMacroIndicators() are callable from frontend components"
    - "BriefingData and MacroIndicators TypeScript types are exported from api.ts"
  artifacts:
    - path: "backend/app/api/macro.py"
      provides: "GET /api/macro/indicators endpoint"
      contains: "get_macro_indicators"
    - path: "frontend/src/lib/api.ts"
      provides: "getBriefing, getMacroIndicators functions + BriefingData, MacroIndicators types"
      exports: ["BriefingData", "MacroIndicators", "getBriefing", "getMacroIndicators"]
  key_links:
    - from: "frontend/src/lib/api.ts"
      to: "http://localhost:8000/api/macro/indicators"
      via: "getMacroIndicators() → apiFetch('/macro/indicators')"
    - from: "frontend/src/lib/api.ts"
      to: "http://localhost:8000/api/briefing/today"
      via: "getBriefing() → apiFetch('/briefing/today')"
---

<objective>
Build the backend foundation that all Phase 5 frontend components depend on. Adds the missing `GET /api/macro/indicators` endpoint to macro.py and extends api.ts with two new functions (`getBriefing`, `getMacroIndicators`) plus their TypeScript types (`BriefingData`, `MacroIndicators`).

Purpose: Unblocks Wave 2 (BriefingCard), Wave 3 (MacroPanel), and satisfies UIUX-04 backend requirement.
Output: Live `/api/macro/indicators` endpoint + typed frontend client functions.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/05-ui-redesign/05-CONTEXT.md
@.planning/phases/05-ui-redesign/RESEARCH.md
@.planning/phases/05-ui-redesign/VALIDATION.md

<interfaces>
<!-- Existing macro.py router pattern (read from file) -->
From backend/app/api/macro.py:
```python
router = APIRouter()
# existing routes: POST /macro/tcmb/scan, POST /macro/tuik/scan, GET /macro/events
# Add new GET /macro/indicators below the existing routes
```

From frontend/src/lib/api.ts — apiFetch signature:
```typescript
async function apiFetch<T>(endpoint: string, options?: FetchOptions): Promise<T>
// endpoint is relative to API_BASE = 'http://localhost:8000/api'
// throws Error(detail) for non-2xx responses
```

From frontend/src/lib/api.ts — api object pattern:
```typescript
export const api = {
  getMacroEvents: (params?) => apiFetch<any>(`/macro/events?...`),
  // Add getMacroIndicators and getBriefing here in the same style
};
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add GET /api/macro/indicators to macro.py</name>
  <files>backend/app/api/macro.py</files>
  <action>
Append a new route to `backend/app/api/macro.py` AFTER the existing `get_macro_events` function. Do NOT modify the existing routes.

The new endpoint:

```python
import asyncio
import time
from functools import lru_cache

# Module-level simple cache (not thread-safe for async but sufficient for single-worker FastAPI)
_indicators_cache: dict = {}
_indicators_cache_ttl = 60  # seconds


@router.get("/macro/indicators")
async def get_macro_indicators():
    """
    Live macro göstergeleri: USD/TRY, altın (TRY), BIST100 endeksi.
    Faiz ve enflasyon sabitleri config'den gelir. 60 saniyelik önbellek.
    """
    global _indicators_cache

    now = time.time()
    if _indicators_cache.get("ts") and now - _indicators_cache["ts"] < _indicators_cache_ttl:
        return _indicators_cache["data"]

    try:
        import yfinance as yf

        tickers = yf.download(
            ["TRY=X", "GC=F", "XU100.IS"],
            period="2d",
            interval="1d",
            progress=False,
            auto_adjust=True,
        )

        def last_close(symbol: str) -> float | None:
            try:
                col = ("Close", symbol)
                series = tickers[col].dropna()
                return float(series.iloc[-1]) if not series.empty else None
            except Exception:
                return None

        usdtry = last_close("TRY=X")
        gold_usd = last_close("GC=F")
        bist100 = last_close("XU100.IS")

        # Convert gold USD/oz → TRY/gram  (1 troy oz = 31.1035 g)
        gold_try = (gold_usd * usdtry / 31.1035) if (gold_usd and usdtry) else None

        # Static policy constants — update manually when TCMB/TUIK publish
        interest_rate = 42.5   # TCMB politika faizi (Nisan 2026)
        inflation_rate = 38.1  # TUIK TÜFE yıllık (Mart 2026)

        result = {
            "usdtry": round(usdtry, 4) if usdtry else None,
            "gold_try": round(gold_try, 2) if gold_try else None,
            "bist100": round(bist100, 2) if bist100 else None,
            "interest_rate": interest_rate,
            "inflation_rate": inflation_rate,
            "as_of": datetime.utcnow().isoformat(),
        }

        _indicators_cache["data"] = result
        _indicators_cache["ts"] = now
        return result

    except Exception as exc:
        logger.error(f"Macro indicators fetch failed: {exc}")
        raise HTTPException(status_code=503, detail=f"Makro veri alınamadı: {exc}")
```

Note: `datetime` is already imported at the top of the file. `yfinance` is already a project dependency — do not add it to requirements.txt.
  </action>
  <verify>
    <automated>cd /Users/nedimkopurlu/Downloads/PROJELER/stalize && /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -c "import ast; ast.parse(open('backend/app/api/macro.py').read()); print('syntax OK')"</automated>
  </verify>
  <done>macro.py parses without syntax errors and contains a `get_macro_indicators` async function with the `/macro/indicators` route decorator.</done>
</task>

<task type="auto">
  <name>Task 2: Add BriefingData, MacroIndicators types and API functions to api.ts</name>
  <files>frontend/src/lib/api.ts</files>
  <action>
Edit `frontend/src/lib/api.ts` to add new types and API functions. Make TWO targeted additions:

**Addition 1 — Types block** (insert after the existing `IntelligenceOverview` interface, before the `// ── API Functions ──` comment line):

```typescript
export interface BriefingData {
  date: string;
  kap_summary: string | null;
  price_summary: string | null;
  macro_summary: string | null;
  notable_stocks: Array<{ symbol: string; reason?: string; direction?: string }> | null;
  ai_commentary: {
    risk_summary?: string | null;
    market_outlook?: string | null;
    [key: string]: unknown;
  } | null;
  created_at: string | null;
  generation_duration_ms: number | null;
}

export interface MacroIndicators {
  usdtry: number | null;
  gold_try: number | null;
  bist100: number | null;
  interest_rate: number | null;
  inflation_rate: number | null;
  as_of: string;
}
```

Note: `notable_stocks` and `ai_commentary` shapes are approximate — the backend stores them as JSON. Add `[key: string]: unknown` index signature to `ai_commentary` to handle unknown subfields safely.

**Addition 2 — API functions** (insert inside the `api` object, after the `getLowCorrelationPairs` function and before the closing `};`):

```typescript
  // ─── FAZ 5: UI Redesign ───

  getBriefing: () => apiFetch<BriefingData>('/briefing/today'),

  getMacroIndicators: () => apiFetch<MacroIndicators>('/macro/indicators'),
```

Do NOT rename or restructure any existing code. Do NOT change the `apiFetch` function. Only append the two type blocks and the two api function entries.
  </action>
  <verify>
    <automated>cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/frontend && npm run build 2>&1 | tail -20</automated>
  </verify>
  <done>
- `npm run build` exits 0 (no TypeScript errors)
- `BriefingData` and `MacroIndicators` are exported from api.ts
- `api.getBriefing` and `api.getMacroIndicators` are callable
  </done>
</task>

</tasks>

<verification>
1. `python3 -c "import ast; ast.parse(open('backend/app/api/macro.py').read())"` — exits 0
2. `cd frontend && npm run build` — exits 0, no TS errors
3. `grep -n "getBriefing\|getMacroIndicators\|BriefingData\|MacroIndicators" frontend/src/lib/api.ts` — all four identifiers present
</verification>

<success_criteria>
- Backend: `GET /api/macro/indicators` route exists in macro.py with 60s cache
- Frontend: `BriefingData`, `MacroIndicators` types exported from api.ts
- Frontend: `api.getBriefing()` and `api.getMacroIndicators()` callable
- TypeScript build clean
</success_criteria>

<output>
After completion, create `.planning/phases/05-ui-redesign/plans/05-01-SUMMARY.md` documenting what was added to macro.py and api.ts, and the exact function signatures created.
</output>
