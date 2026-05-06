# Phase 29: Dashboard - Research

**Researched:** 2026-05-05
**Domain:** Next.js frontend — dashboard page rewrite, market widget layout, API client extension
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** `frontend/src/app/page.tsx` tamamen silinip sıfırdan yazılır. Eski kodun hiçbir parçası korunmaz.
- **D-02:** `page.module.css` de sıfırdan yazılır; yalnızca yeni dashboard için gerekli stiller kalır.
- **D-03:** Sayfanın en üstünde BIST100 tam genişlikte (full-width) banner.
- **D-04:** BIST100 banner'ın altında esnek grid: Döviz widgetı ve Altın widgetı yan yana (masaüstünde 2 kolon, mobilde 1 kolon).
- **D-05:** En altta portföy özet widgetı (tam genişlikte veya grid içinde tek satır).
- **D-06:** Her döviz çifti için: sembol, fiyat, günlük % değişim, yön ok işareti (▲/▼). Sparkline yok.
- **D-07:** Altın widgetı: gram, ons, çeyrek, yarım, tam — her biri TRY fiyatı + % değişim + ok rengi.
- **D-08:** BIST100 banner: Endeks değeri, günlük % değişim (yeşil/kırmızı), hacim. Değişim işareti büyük ve net okunur.
- **D-09:** Sayfa açılışında veri çekilir (useEffect), ardından her 30 saniyede otomatik yenileme. `setInterval`/`clearInterval` lifecycle temizleme.
- **D-10:** Her endpoint bağımsız olarak non-blocking şekilde yüklenir — BIST100, forex, gold ayrı state'ler.
- **D-11:** Portföy widgetı alanı tasarımda yer alır ama Phase 32 tamamlanana kadar "Portföy henüz eklenmedi — yakında" boş durum mesajı gösterir.
- **D-12:** Mevcut CSS custom properties kullanılır. Yeni CSS sınıfı tanımlanmaz — mevcut `card`, `glass-card` sınıfları önceliklidir.
- **D-13:** `AppShell` ve `Sidebar` aynen korunur, yalnızca page içeriği değişir.
- **D-14:** Tamamen Türkçe etiketler.

### Claude's Discretion

- Döviz çiftlerinin sırası ve hangi 6 çiftin gösterileceği (FOREX_PAIRS tanımlı: USD, EUR, GBP, CNY, JPY, CHF)
- Sayı formatı (binlik ayraç, ondalık basamak sayısı) — formatPrice() helper kullanılabilir
- Loading skeleton tasarımı
- Error state (kart başına mı, sayfa genelinde mi?)

### Deferred Ideas (OUT OF SCOPE)

- BIST100 sparkline grafiği — Phase 30 veya sonrasına bırakılır
- Döviz alarm / trend notification — v2 kapsamında
- Altın tarihsel grafik — Hisse Detay mantığı tamamlandıktan sonra
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DASH-01 | Kullanıcı BIST100 endeks özetini görür (günlük değişim, hacim) | `/api/market/bist100` returns `{ value, daily_change_pct, volume, as_of }` — banner widget consumes this |
| DASH-02 | Kullanıcı 5-10 döviz çiftini takip eder (USD/TRY, EUR/TRY, GBP/TRY vb.) | `/api/market/forex` returns `{ pairs: [...], count, as_of }` — 6 pairs from FOREX_PAIRS constant |
| DASH-03 | Kullanıcı altın fiyatlarını takip eder (gram, ons, çeyrek, yarım, tam) | `/api/market/gold` returns `{ forms: { gram, ons, ceyrek, yarim, tam }, gold_usd_per_oz, usdtry, as_of }` |
| DASH-04 | Kullanıcı portföy özetini görür (toplam değer, günlük değişim) | Phase 32 is prerequisite; Phase 29 renders placeholder card with `TerminalEmpty` |
</phase_requirements>

---

## Summary

Phase 29 is a **pure frontend rewrite** of `frontend/src/app/page.tsx`. The backend is already complete (Phase 28 delivered all three `/api/market/*` endpoints). The work is entirely in the React/Next.js layer: extend `api.ts` with three new typed methods, rewrite `page.tsx` to fetch from those endpoints with independent non-blocking state, and rewrite `page.module.css` with the minimal CSS the new layout needs.

The key architectural pattern is already established in the codebase: `'use client'` + `useEffect` + `Promise.allSettled` per independent data domain. The new page follows this exact pattern with three separate state buckets (bist100, forex, gold) plus a 30-second `setInterval` refresh loop. AppShell and Sidebar are untouched.

**Primary recommendation:** Keep 100% of the implementation inside `page.tsx` and `page.module.css`. Do not introduce new component files — all widget rendering is local sub-functions at the bottom of `page.tsx`, following the established pattern from the existing file. Only `api.ts` needs external modification.

---

## Standard Stack

### Core (already installed, no new packages needed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 19.2.4 | UI rendering + hooks (`useState`, `useEffect`) | Project standard |
| Next.js | 16.2.3 (App Router) | Page routing, `'use client'` directive | Project standard |
| TypeScript | 5.x | Type safety for API response shapes | Project standard |

### Reused Project Components

| Component | Source | Usage in Phase 29 |
|-----------|--------|-------------------|
| `AppShell` | `@/components/AppShell.tsx` | Page wrapper — untouched |
| `Sidebar` | `@/components/Sidebar.tsx` | Nav — untouched |
| `TerminalPageHeader` | `@/components/TerminalPrimitives.tsx` | Page title "Piyasa Özeti" + description |
| `TerminalError` | `@/components/TerminalPrimitives.tsx` | Per-widget error display |
| `TerminalEmpty` | `@/components/TerminalPrimitives.tsx` | Portfolio placeholder empty state |
| `PriceChange` | `@/components/StockHelpers.tsx` | ▲/▼ arrow + colored % change for every price change value |
| `formatPrice` | `@/components/StockHelpers.tsx` | TRY price format (tr-TR locale, 2 decimal, thousands dot) |
| `formatVolume` | `@/components/StockHelpers.tsx` | Volume abbreviation (M/B/K) for BIST100 hacim |

**Installation:** No new packages required. All dependencies are present.

---

## Architecture Patterns

### Recommended Project Structure

No new files besides the two being rewritten:
```
frontend/src/app/
├── page.tsx          ← REWRITE (was 510 lines; new ~220 lines)
└── page.module.css   ← REWRITE (was ~1347 lines of old dashboard; new ~120 lines)
frontend/src/lib/
└── api.ts            ← ADD 3 methods + 3 interfaces (append-only, no deletions)
```

### Pattern 1: Independent Non-Blocking Parallel Fetch

**What:** Three separate state buckets, each independently fetched. No shared loading/error state.
**When to use:** Whenever multiple unrelated data sources populate different page sections.
**Example (verified from existing page.tsx lines 51–71):**

```typescript
// Source: existing frontend/src/app/page.tsx lines 51-71
// BIST100 — non-blocking
api.getMacroIndicators()
  .then(setMacroIndicators)
  .catch(() => setMacroIndicators(null))
  .finally(() => setMacroLoading(false));
```

For Phase 29, the same pattern applies with `getMarketBist100()`, `getMarketForex()`, `getMarketGold()` — each `.then(set*)` / `.catch(() => setError*)` / `.finally(() => setLoading*(false))`.

### Pattern 2: setInterval Auto-Refresh with Cleanup

**What:** 30-second polling loop started after initial load.
**When to use:** D-09 requires auto-refresh every 30 seconds.

```typescript
// Established React pattern for interval cleanup
useEffect(() => {
  fetchAll();
  const id = setInterval(fetchAll, 30_000);
  return () => clearInterval(id);
}, []);
```

**Critical:** The cleanup `return` prevents memory leaks on unmount and React StrictMode double-invoke. `fetchAll` must not show skeleton during refresh — check `if (!bist100Loading && !forexLoading && !goldLoading)` before showing skeletons (only show skeleton on first load when data is `null`).

### Pattern 3: Local Sub-Component Functions

**What:** Helper render functions defined at the bottom of `page.tsx`, not exported as separate component files.
**When to use:** Widget-level rendering that is local to this page only.
**Example (verified from existing page.tsx lines 451–510):**

```typescript
// Source: existing frontend/src/app/page.tsx
function StatCard({ label, value, icon, accent }: { ... }) { ... }
function PortfolioSignal({ label, value, tone }: { ... }) { ... }
```

Phase 29 will define `Bist100Banner`, `ForexWidget`, `GoldWidget`, `PortfolioPlaceholder` as local functions with the same pattern.

### Pattern 4: API Client Extension

**What:** Append new typed interfaces and methods to `api.ts`.
**When to use:** Any new backend endpoint needs a typed frontend method.

New types needed (append to api.ts after existing interfaces):

```typescript
export interface MarketBist100Response {
  value: number | null;
  daily_change_pct: number | null;
  volume: number | null;
  as_of: string;
}

export interface ForexPair {
  symbol: string;       // e.g. "USDTRY=X"
  name: string;         // e.g. "USD/TRY"
  rate: number | null;
  daily_change_pct: number | null;
  as_of: string;
}

export interface MarketForexResponse {
  pairs: ForexPair[];
  count: number;
  as_of: string;
}

export interface MarketGoldResponse {
  forms: {
    gram: number | null;
    ons: number | null;
    ceyrek: number | null;
    yarim: number | null;
    tam: number | null;
  };
  gold_usd_per_oz: number | null;
  usdtry: number | null;
  as_of: string | null;
}
```

New methods added to the `api` object:
```typescript
getMarketBist100: () => apiFetch<MarketBist100Response>('/market/bist100'),
getMarketForex: () => apiFetch<MarketForexResponse>('/market/forex'),
getMarketGold: () => apiFetch<MarketGoldResponse>('/market/gold'),
```

### Anti-Patterns to Avoid

- **Blocking render on all-or-nothing load:** Do NOT use a single `loading` state that blocks the whole page. Each widget must be independently loadable (D-10).
- **Re-implementing formatters:** Do NOT write custom number formatting. Use `formatPrice()`, `formatVolume()`, `PriceChange` from StockHelpers.tsx.
- **New component files:** Do NOT create `Bist100Banner.tsx`, `ForexWidget.tsx`, etc. as separate files. They are local sub-functions in `page.tsx`.
- **Adding CSS variables:** Do NOT define new `--custom-*` variables. Use only the ones declared in `globals.css`.
- **Reusing old page.module.css classes:** The file is rewritten from scratch. Classes like `.statsGrid`, `.portfolioGrid`, `.mainLayout` are removed. Only the 10 new classes from the UI-SPEC are written.
- **Showing skeleton during refresh:** Once data exists in state, refresh silently. Only show skeleton on initial null state.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Price formatting (tr-TR locale) | Custom `toLocaleString` call | `formatPrice()` in StockHelpers.tsx | Already handles null, locale, 2 decimal |
| Positive/negative % change with arrow | Custom span with conditional class | `PriceChange` component in StockHelpers.tsx | Already handles null, ▲/▼, green/red |
| Volume abbreviation (M/B/K) | Custom conditional string | `formatVolume()` in StockHelpers.tsx | Already handles B/M/K thresholds |
| Error display in widget | Custom error div | `TerminalError` from TerminalPrimitives.tsx | Project-standard error primitive |
| Empty state | Custom placeholder div | `TerminalEmpty` from TerminalPrimitives.tsx | Project-standard empty primitive |
| Page title + description header | Custom h1/p block | `TerminalPageHeader` from TerminalPrimitives.tsx | Consistent with all other pages |
| Shimmer loading animation | Custom CSS animation | `.skeleton` global class (globals.css) | `@keyframes shimmer` already defined |

---

## Backend API Contract (Phase 28 — verified from source)

### GET /api/market/bist100
Response shape (verified from `backend/app/api/market.py` lines 90-95):
```json
{
  "value": 10500.0,
  "daily_change_pct": 5.0,
  "volume": null,
  "as_of": "2026-05-05"
}
```
- `volume` is `null` when XU100 reports 0 or NaN (index volume unreliable — Pitfall 1 from Phase 28)
- Returns HTTP 503 if no rows exist in DB

### GET /api/market/forex
Response shape (verified from `backend/app/api/market.py` lines 130-138):
```json
{
  "pairs": [
    { "symbol": "USDTRY=X", "name": "USD/TRY", "rate": 32.4507, "daily_change_pct": 0.12, "as_of": "2026-05-05" },
    ...
  ],
  "count": 6,
  "as_of": "2026-05-05T..."
}
```
- Pairs with no DB rows are silently skipped (count may be < 6)
- `daily_change_pct` is `null` when only 1 row exists for that symbol

### GET /api/market/gold
Response shape (verified from `backend/app/api/market.py` lines 232-241):
```json
{
  "forms": {
    "gram": 3245.12,
    "ons": 100887.5,
    "ceyrek": 5694.74,
    "yarim": 11389.48,
    "tam": 22778.96
  },
  "gold_usd_per_oz": 3250.0,
  "usdtry": 32.4507,
  "as_of": "2026-05-05"
}
```
- Returns HTTP 503 if GC=F (gold) or USDTRY=X is missing from DB
- No `daily_change_pct` on gold forms — endpoint does not compute it (Phase 29 cannot display gold change %)

**IMPORTANT FINDING — Gold change_pct unavailable:** The `/api/market/gold` endpoint (Phase 28 implementation) does NOT return `daily_change_pct` for gold forms. The UI-SPEC (D-07) lists "% değişim" for altın widgetı, but the backend only returns computed prices. The plan must either: (a) display "—" for gold change %, or (b) treat this as a Phase 28 backend gap to address. **Recommendation: Display "—" for gold change % until backend extends the gold endpoint — this is consistent with `formatPrice(null)` → "—" pattern.** Document this as a known limitation.

---

## CSS Contract (from UI-SPEC, globals.css inspection)

### Global classes available (no re-definition needed)
| Class | Source | Usage |
|-------|--------|-------|
| `.card` | globals.css line 190 | 24px padding, backdrop-filter blur(20px), border-radius 12px |
| `.glass-card` | globals.css line 635 | glass variant for cards |
| `.skeleton` | globals.css line 440 | shimmer animation placeholder |
| `.text-green` | globals.css line 481 | `color: var(--green-400)` |
| `.text-red` | globals.css line 482 | `color: var(--red-400)` |
| `.text-muted` | globals.css | `color: var(--text-muted)` |
| `.font-mono` | globals.css line 488 | monospace font |
| `.animate-fade-in` | globals.css line 472 | fade-in animation |

### New classes in page.module.css (from UI-SPEC CSS Modules Contract)
| Class | Purpose |
|-------|---------|
| `.bist100Banner` | Full-width flex container |
| `.bist100Value` | Endeks değeri — 28px mono weight 700 |
| `.bist100Change` | % değişim — 28px weight 700, conditional green/red |
| `.bist100Meta` | Hacim etiketi — 14px uppercase letter-spacing 0.05em |
| `.marketGrid` | 2-column grid; 1fr 1fr; collapses to 1fr at ≤768px |
| `.widgetHeader` | Widget card header — justify-content space-between |
| `.widgetTitle` | 20px/700 heading |
| `.widgetRefreshHint` | "Otomatik yenileme: Xs" — accent-cyan, 14px mono uppercase |
| `.pairRow` | Forex/altın row — flex, space-between, border-bottom |
| `.pairLabel` | 14px/700 pair name |
| `.pairPrice` | 14px mono/700 price value |
| `.portfolioPlaceholder` | Dashed border card for empty portfolio |

---

## Common Pitfalls

### Pitfall 1: Gold `daily_change_pct` Not Available from Backend
**What goes wrong:** UI-SPEC shows gold change % arrows, but `/api/market/gold` endpoint (Phase 28) only computes current prices from `gram_try * weight`. No previous-day row lookup is performed.
**Why it happens:** The endpoint was designed to show current prices; change calculation was not part of Phase 28 scope.
**How to avoid:** Render "—" for gold change % using the `PriceChange` component with `value={null}`. Do not attempt to derive change from two sequential gold API calls.
**Warning signs:** Undefined or missing `change_pct` key on gold forms.

### Pitfall 2: setInterval and React StrictMode Double-Invoke
**What goes wrong:** In development, React StrictMode runs effects twice. If the interval is started in `useEffect` without cleanup, two intervals will fire.
**Why it happens:** StrictMode intentionally unmounts and remounts to detect side effects.
**How to avoid:** Always return `() => clearInterval(id)` from the `useEffect` that starts the interval.
**Warning signs:** Data refreshes at ~15s instead of 30s in development.

### Pitfall 3: Skeleton Flash During Refresh
**What goes wrong:** If skeleton is shown whenever `loading` is true, users see a flash every 30 seconds.
**Why it happens:** Setting `setLoading(true)` before `setInterval` refresh clears the displayed data.
**How to avoid:** Track initial load vs. refresh separately. Show skeleton only when `data === null` (never loaded yet), not when `data !== null` but loading is in progress.

### Pitfall 4: Missing Null Guard on `volume`
**What goes wrong:** BIST100 `volume` is `null` when index reports 0 (D-08 / Phase 28 Pitfall 1). Calling `formatVolume(null)` returns "—" correctly, but passing `undefined` crashes.
**Why it happens:** API response destructuring may return `undefined` if field is absent.
**How to avoid:** Type as `number | null` and use `bist100?.volume ?? null` before passing to `formatVolume`.

### Pitfall 5: forex pairs order is dict-ordered from backend
**What goes wrong:** `pairs` array from `/api/market/forex` is iterated in `FOREX_PAIRS` dict order (Python 3.7+ insertion order). The order is: USD, EUR, GBP, CNY, JPY, CHF. If the frontend sorts or re-orders, it breaks the contract.
**Why it happens:** Backend iterates `FOREX_PAIRS.items()` in insertion order.
**How to avoid:** Render pairs in the order returned by the API. Do not sort on frontend. The order matches the UI-SPEC: USD/TRY → EUR/TRY → GBP/TRY → CNY/TRY → JPY/TRY → CHF/TRY.

### Pitfall 6: `TerminalShell` wrapper required
**What goes wrong:** Other pages in the project wrap content in `<TerminalShell>` after `<AppShell>`. Omitting it breaks the terminal-style content layout.
**Why it happens:** `TerminalShell` applies the `.shell` CSS class from `terminal.module.css` which provides content width and padding.
**How to avoid:** Wrap page content as `<AppShell><TerminalShell>...</TerminalShell></AppShell>`. Verify by checking existing pages (stocks/page.tsx, etc.).

---

## Code Examples

### Refresh Hint Countdown Pattern

```typescript
// Track seconds until next refresh
const [countdown, setCountdown] = useState(30);

useEffect(() => {
  fetchAll();
  let secs = 30;
  const tick = setInterval(() => {
    secs -= 1;
    if (secs <= 0) {
      secs = 30;
      fetchAll();
    }
    setCountdown(secs);
  }, 1_000);
  return () => clearInterval(tick);
}, []);
```

This gives a live "Otomatik yenileme: 29s" countdown (from UI-SPEC copywriting contract).

### Per-Widget Error State

```typescript
// Independent error state per widget (D-10)
const [bist100Error, setBist100Error] = useState<string | null>(null);
const [forexError, setForexError] = useState<string | null>(null);
const [goldError, setGoldError] = useState<string | null>(null);
```

In render, each widget checks its own error:
```tsx
{forexError
  ? <TerminalError>{forexError}</TerminalError>
  : forexLoading && !forex
    ? <ForexSkeleton />
    : <ForexList pairs={forex?.pairs ?? []} />
}
```

### Forex Turkish Label Map

```typescript
// Required by D-14 — Türkçe etiketler
const FOREX_TR_LABELS: Record<string, string> = {
  'USDTRY=X': 'Dolar',
  'EURTRY=X': 'Avro',
  'GBPTRY=X': 'Sterlin',
  'CNYTRY=X': 'Çin Yuanı',
  'JPYTRY=X': 'Japon Yeni',
  'CHFTRY=X': 'İsviçre Frangı',
};
```

### Gold Turkish Label Map

```typescript
// Altın form labels — D-07 / UI-SPEC Altın Widget Sırası
const GOLD_TR_LABELS: Record<string, string> = {
  gram: 'Gram Altın',
  ons: 'Ons Altın',
  ceyrek: 'Çeyrek Altın',
  yarim: 'Yarım Altın',
  tam: 'Tam Altın',
};
const GOLD_FORM_ORDER = ['gram', 'ons', 'ceyrek', 'yarim', 'tam'] as const;
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `page.tsx` fetching old `/api/dashboard`, macro, KAP, sparklines, model portfolio, portfolio | `page.tsx` fetching only `/api/market/bist100`, `/api/market/forex`, `/api/market/gold` | Phase 29 (now) | 5 API calls → 3 calls; page loads faster |
| Single `loading` state gates entire page | Per-widget loading state; page always renders shell | Phase 29 (now) | Better perceived performance |
| Manual `loadData()` button + initial useEffect | Auto-refresh every 30s via setInterval | Phase 29 (now) | Always-live data |

**Removed from old page (do not re-introduce):**
- `MacroPanel` import and usage (old macro indicators panel)
- `SparklineWidget` imports (deferred to later phase)
- `ScoreRing` (stock scoring — belongs in Phase 30 discovery)
- `KapNotification` feed (belongs in Phase 31 news)
- `ModelPortfolio` data (belongs in Phase 33)
- All old `DashboardData`, `KapNotification`, `SparklineResponse`, `ModelPortfolioCurrentResponse` type imports from api.ts (do NOT delete these types — they may be used by other pages)

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (backend only); no frontend test framework detected |
| Config file | `backend/tests/` directory; no `pytest.ini` — tests run from backend root |
| Quick run command | `cd backend && python -m pytest tests/test_market_endpoints.py -x -q` |
| Full suite command | `cd backend && python -m pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DASH-01 | BIST100 banner renders with value + change_pct | manual smoke | — | N/A (frontend) |
| DASH-02 | Forex widget renders 6 pairs with rates | manual smoke | — | N/A (frontend) |
| DASH-03 | Gold widget renders 5 forms with TRY prices | manual smoke | — | N/A (frontend) |
| DASH-04 | Portfolio placeholder renders with dashed border | manual smoke | — | N/A (frontend) |
| DASH-01 backend | `/api/market/bist100` returns value + change_pct | integration | `pytest tests/test_market_endpoints.py::test_bist100_endpoint_returns_value_and_change -x` | ✅ |
| DASH-02 backend | `/api/market/forex` returns pairs list | integration | `pytest tests/test_market_endpoints.py -k "forex" -x` | ✅ |
| DASH-03 backend | `/api/market/gold` returns forms dict | integration | `pytest tests/test_market_endpoints.py -k "gold" -x` | ✅ |

### Sampling Rate
- **Per task commit:** `cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && python -m pytest tests/test_market_endpoints.py -x -q`
- **Per wave merge:** `cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && python -m pytest tests/ -x -q`
- **Phase gate:** Backend tests green + manual browser verification of all 4 widgets before `/gsd:verify-work`

### Wave 0 Gaps
None for backend — `tests/test_market_endpoints.py` already covers all three market endpoints from Phase 28. No frontend unit tests exist in this project (no jest/vitest detected). Frontend validation is manual smoke testing only.

---

## Open Questions

1. **Gold `daily_change_pct` display**
   - What we know: `/api/market/gold` does not return change_pct for forms; only current prices.
   - What's unclear: Should Phase 29 leave gold change as "—", or should this be a Phase 28 backend fix?
   - Recommendation: Render "—" via `PriceChange` with `value={null}`. Add a comment in code noting this gap. Do not block Phase 29 on this.

2. **`TerminalShell` wrapper requirement**
   - What we know: All other pages wrap content in `<AppShell><TerminalShell>`. The old `page.tsx` uses this pattern (line 157).
   - What's unclear: Whether `TerminalShell` is strictly required or optional.
   - Recommendation: Include `TerminalShell` per established project pattern. It provides layout padding and max-width.

---

## Sources

### Primary (HIGH confidence)
- `backend/app/api/market.py` — endpoint shapes verified from source (lines 53-243)
- `frontend/src/app/page.tsx` — existing pattern verified from source (510 lines)
- `frontend/src/lib/api.ts` — existing api client pattern verified (915 lines)
- `frontend/src/components/StockHelpers.tsx` — formatter functions verified
- `frontend/src/components/TerminalPrimitives.tsx` — available primitives verified
- `frontend/src/app/globals.css` — CSS variables, `.card`, `.skeleton`, `.glass-card` verified
- `frontend/src/app/page.module.css` — existing classes verified (will be fully replaced)
- `.planning/phases/29-dashboard/29-CONTEXT.md` — all decisions verified
- `.planning/phases/29-dashboard/29-UI-SPEC.md` — layout contract verified

### Secondary (MEDIUM confidence)
- `backend/tests/test_market_endpoints.py` — test coverage for Phase 28 endpoints confirmed

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified from package.json, imports, existing files
- Architecture: HIGH — verified from existing `page.tsx` patterns and CONTEXT.md decisions
- Pitfalls: HIGH — gold change_pct gap verified from backend source code
- API shapes: HIGH — verified from `market.py` source directly

**Research date:** 2026-05-05
**Valid until:** 2026-06-05 (stable stack; Phase 28 backend is locked)
