# Phase 34: Frontend Tasarım Düzeltmeleri - Research

**Researched:** 2026-05-08
**Domain:** Next.js 15 App Router, CSS Modules, TypeScript, inline SVG
**Confidence:** HIGH — all findings are from direct file inspection (no training-data assumptions)

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DESIGN-01 | Dashboard BIST100 grafiği 6 periyot tabını gösterir (1G, 1H, 1A, 3A, 1Y, Tüm); 1G/1H için mock veri kullanılır | chartPeriod union type + Bist100Chart `n=` logic confirmed; seedSeries NOT present in page.tsx — must be added |
| DESIGN-02 | Kazananlar/kaybedenler satırlarında 40×28px mini sparkline görünür | StockRows sub-component identified; grid-template-columns must gain a sparkline column; inline SVG polyline pattern confirmed |
| DESIGN-03 | Model portföy sayfası 6 strateji kartını gösterir | page.tsx is 155 lines with 0 strategy cards; CSS module has no card styles yet — all must be added |
| DESIGN-04 | Light mode hover background değişkeni kullanır | Hardcoded `rgba(255,255,255,.03)` at page.module.css line 373; fix is one-liner |
| DESIGN-05 | SparklineWidget.tsx silindi; api.ts'ten kullanılmayan metodlar ve orphan interfaces kaldırıldı | SparklineWidget: zero external imports confirmed. Dead methods: getSourceCatalog, scanSource, getSourceHealthHistory. Orphan interfaces: SourceCatalogItem, SourceCatalogResponse, SourceHealthHistoryItem, SourceHealthHistoryResponse, SourceHealthRollupItem, SourceHealthDashboardResponse, SourceHealthAlertItem — also SparklinePoint, SparklineResponse (only used in SparklineWidget) |
| DESIGN-06 | Dashboard portföy kartı pozisyon yokken /portföy'e yönlendiren boş durum mesajı gösterir | Current code at line 234 already has a Link but text is minimal "Pozisyon ekle"; needs richer empty-state CTA block |
</phase_requirements>

---

## Summary

Phase 34 is a pure frontend polish phase: no new API endpoints, no database changes, no backend work. All six DESIGN requirements are confined to three files in `frontend/src/`: `app/page.tsx`, `app/page.module.css`, `app/model-portfolio/page.tsx` + `app/model-portfolio/page.module.css`, plus deletion of `components/SparklineWidget.tsx` and trimming of `lib/api.ts`.

Every finding below is sourced from direct code inspection of the current repo state. Confidence is HIGH throughout because the work is surgical edits to files that are fully readable.

**Primary recommendation:** Group changes into two plans as the roadmap already states — Plan 34-01 (DESIGN-01 + DESIGN-02, both in `page.tsx`) and Plan 34-02 (DESIGN-03 + DESIGN-04 + DESIGN-05 + DESIGN-06, spread across model-portfolio files, page.module.css, api.ts, and SparklineWidget deletion).

---

## Standard Stack

### Core (already installed — no new installs needed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 19.2.4 | Component rendering | Project stack |
| Next.js | 16.2.3 | App Router, Link | Project stack |
| CSS Modules | built-in | Scoped styles | Established pattern in all pages |
| Inline SVG | browser-native | Mini sparklines | Zero dependency; already used in `Bist100Chart` and the sidebar icon pattern |

### No New Dependencies

All six fixes can be implemented with what is already in the repo:
- Sparklines: inline SVG `<polyline>` — same technique used in `Bist100Chart` in `page.tsx`
- Mock/seed data for 1G/1H: deterministic math (no library)
- Strategy cards: static JSX + new CSS Module classes
- Dead code removal: file deletion + line deletion

**Installation:** none required.

---

## Architecture Patterns

### Recommended Project Structure (unchanged)

```
frontend/src/
├── app/
│   ├── page.tsx                  # DESIGN-01, DESIGN-02, DESIGN-06 edits
│   ├── page.module.css           # DESIGN-04 fix
│   └── model-portfolio/
│       ├── page.tsx              # DESIGN-03: add 6 strategy cards
│       └── page.module.css       # DESIGN-03: add card CSS
├── components/
│   └── SparklineWidget.tsx       # DESIGN-05: DELETE this file
└── lib/
    └── api.ts                    # DESIGN-05: remove 3 methods + 7 interfaces
```

### Pattern 1: Inline SVG Sparkline (for DESIGN-02)

**What:** 40×28px `<svg>` polyline drawn from an array of numbers using min/max normalization.
**When to use:** Whenever a miniature trend line is needed inside a list row — no library dependency, no re-render cost.

The `Bist100Chart` function in `page.tsx` (lines 24–64) already demonstrates this pattern at scale. For stock-row sparklines, the same technique at 40×28 resolution is sufficient.

```tsx
// Derived from Bist100Chart in frontend/src/app/page.tsx
function MiniSparkline({ values, up }: { values: number[]; up: boolean }) {
  if (values.length < 2) return <div style={{ width: 40, height: 28 }} />;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const W = 40; const H = 28;
  const pts = values.map((v, i) =>
    `${((i / (values.length - 1)) * W).toFixed(1)},${(H - ((v - min) / range) * (H - 4) - 2).toFixed(1)}`
  ).join(' ');
  const color = up ? 'var(--accent-green)' : 'var(--accent-red)';
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5"
        strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
```

### Pattern 2: Deterministic Seed Series (for DESIGN-01, DESIGN-02)

**What:** A pure function that takes a symbol string (or period label) as a seed and returns a stable array of plausible numbers.
**When to use:** When real data is unavailable (1G/1H intraday) but an empty chart would break the UI.

Note: The additional context mentions `seedSeries()` exists in `page.tsx` — but it is NOT present in the current file (lines 1–447). It must be authored from scratch. The pattern is simple deterministic pseudo-random using string char-codes:

```tsx
// To be written in page.tsx
function seedSeries(seed: string, n: number, base = 9000, spread = 400): number[] {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) >>> 0;
  return Array.from({ length: n }, (_, i) => {
    h = (h * 1664525 + 1013904223) >>> 0;
    const noise = ((h >>> 16) / 65535 - 0.5) * spread;
    return base + noise + (i / n) * 100;
  });
}
```

Usage: `seedSeries('1G', 48, bist100?.value ?? 9000)` for 48 half-hour points.

### Pattern 3: chartPeriod Type Extension (for DESIGN-01)

Current type at `page.tsx` line 105:
```tsx
const [chartPeriod, setChartPeriod] = useState<'1A' | '3A' | '1Y' | 'Tüm'>('1A');
```

Must become:
```tsx
const [chartPeriod, setChartPeriod] = useState<'1G' | '1H' | '1A' | '3A' | '1Y' | 'Tüm'>('1A');
```

And the period tabs map at line 191 must include `'1G'` and `'1H'`:
```tsx
{(['1G', '1H', '1A', '3A', '1Y', 'Tüm'] as const).map((p) => ...)}
```

The `Bist100Chart` component's `visiblePoints` useMemo at line 34 must handle `'1G'` and `'1H'`:
```tsx
const n = period === '1G' ? 0 /* use seed */ : period === '1H' ? 0 /* use seed */
        : period === '1A' ? 30 : period === '3A' ? 90 : period === '1Y' ? 252 : points.length;
```

However because 1G/1H have zero real points, a cleaner approach is to pass seed data as the `points` prop from the parent (keeping `Bist100Chart` stateless), or accept a `seedValues` override prop.

**Recommended approach:** Extend `Bist100Chart` to accept an optional `seedValues?: number[]` prop. When `period` is `'1G'` or `'1H'` and `seedValues` is provided, use those instead of slicing from `bistHistory.points`.

### Pattern 4: StockRow Grid Extension (for DESIGN-02)

Current `.stockRow` grid at `page.module.css` line 360:
```css
grid-template-columns: 52px 1fr 68px 68px;
```

Must add a sparkline column (40px wide):
```css
grid-template-columns: 52px 1fr 40px 68px 68px;
```

And `StockRows` sub-component at `page.tsx` line 338 must inject `<MiniSparkline>` between the name and price columns.

Each stock row needs its own seed values. Use `seedSeries(s.symbol, 20, s.current_price ?? 100)` to get 20 plausible points derived deterministically from the symbol string.

### Pattern 5: Model Portfolio Strategy Cards (for DESIGN-03)

The 6 strategy cards are purely static display — no API call, no state. They should be defined as a constant array and rendered in a grid.

**Card data:**

```tsx
const STRATEGIES = [
  {
    id: 'temettu',
    icon: '💰',
    name: 'Temettü Avcısı',
    desc: 'Yüksek ve istikrarlı temettü ödeyen hisseler; pasif gelir odaklı.',
    badge: 'Defansif',
    color: 'var(--accent-green)',
  },
  {
    id: 'buyume',
    icon: '🚀',
    name: 'Büyüme Lokomotifleri',
    desc: 'Güçlü gelir büyümesi ve pazar payı kazanan sektör liderleri.',
    badge: 'Agresif',
    color: 'var(--accent-blue)',
  },
  {
    id: 'defansif',
    icon: '🛡️',
    name: 'Defansif Kalkan',
    desc: 'Dayanıklı tüketim ve kamu hizmetleri; piyasa dalgalanmalarına karşı koruma.',
    badge: 'Düşük Risk',
    color: 'var(--accent-indigo)',
  },
  {
    id: 'momentum',
    icon: '⚡',
    name: 'Momentum',
    desc: 'Son 3-6 ayda güçlü fiyat ivmesi gösteren, trend sürebilecek hisseler.',
    badge: 'Aktif',
    color: 'var(--accent)',
  },
  {
    id: 'deger',
    icon: '🔍',
    name: 'Değer Yatırımı',
    desc: 'Düşük F/K ve PD/DD ile gerçek değerinin altında işlem gören hisseler.',
    badge: 'Uzun Vade',
    color: 'var(--accent-purple)',
  },
  {
    id: 'karma',
    icon: '⚖️',
    name: 'Karma',
    desc: 'Temettü, büyüme ve değer unsurlarını dengeleyen çeşitli portföy.',
    badge: 'Dengeli',
    color: 'var(--text-muted)',
  },
] as const;
```

Cards render below the existing `AiPortfolioSection`. Add a section heading "Strateji Şablonları" and a CSS grid (2 or 3 columns responsive).

### Anti-Patterns to Avoid

- **Don't add a new SparklineWidget import to get sparklines** — the component being deleted uses heavyweight `lightweight-charts`; use inline SVG instead.
- **Don't create a new `seedSeries` utility file** — put it as a module-level function in `page.tsx` only; it's not shared.
- **Don't convert strategy cards to client state** — they are static constants, no `useState` or API call.
- **Don't use hardcoded dark-mode rgba values** in hover states — always use CSS custom properties defined in `globals.css`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Sparkline chart | lightweight-charts integration | Inline SVG polyline | Zero deps, already used in Bist100Chart |
| Mock data randomness | crypto.getRandomValues or Math.random | Deterministic LCG from symbol seed | Stable across re-renders |

---

## Common Pitfalls

### Pitfall 1: chartPeriod TypeScript Union Not Updated
**What goes wrong:** Adding '1G'/'1H' to the JSX array but not to the `useState` type annotation causes a TypeScript build error.
**Why it happens:** TypeScript strict mode; the `as const` assertion on the array makes the literal types mandatory.
**How to avoid:** Update both the `useState` generic and the array literal in the same edit.
**Warning signs:** `TS2345` type error during `npm run build`.

### Pitfall 2: Light Mode Hover Still Invisible
**What goes wrong:** Changing the hex/rgba in page.module.css doesn't fix the issue if the rule is duplicated elsewhere (e.g., a global `.stockRow:hover` rule).
**Why it happens:** CSS specificity; a global rule may override the module rule.
**How to avoid:** After the fix, verify in light mode with browser devtools — confirm the background is visible (rgba(0,0,0,.04) on white = subtle grey).
**Warning signs:** Hover still looks invisible or has wrong color in DevTools "Computed" panel.

### Pitfall 3: Deleting Interfaces That Are Still Transitively Used
**What goes wrong:** Deleting `SourceHealthHistoryItem` while `SourceHealthRollupItem` still references it causes a build error.
**Why it happens:** Interfaces reference each other.
**How to avoid:** Delete the entire cluster in one pass in this order (dependency order, most referenced last):
  1. `SourceHealthAlertItem` (no deps)
  2. `SourceHealthHistoryItem` (dep of SourceHealthRollupItem, SourceHealthDashboardResponse)
  3. `SourceCatalogItem` (dep of SourceCatalogResponse, SourceHealthRollupItem, SourceHealthDashboardResponse)
  4. `SourceCatalogResponse` (dep of SourceHealthDashboardResponse)
  5. `SourceHealthHistoryResponse`
  6. `SourceHealthRollupItem`
  7. `SourceHealthDashboardResponse`
  8. `SparklinePoint` (dep of SparklineResponse)
  9. `SparklineResponse`
  And methods: `getSourceCatalog`, `scanSource`, `getSourceHealthHistory`.
**Warning signs:** TypeScript `TS2304 Cannot find name 'X'` errors.

### Pitfall 4: MiniSparkline Causes Layout Shift
**What goes wrong:** Adding a 40px sparkline column to `.stockRow` grid makes the row wider than the card, causing overflow.
**Why it happens:** The total of `52+auto+40+68+68 = 228px + flex-1` may exceed the `.colCard` width on narrow screens.
**How to avoid:** The column is only 40px. The `.stockName` column uses `1fr` (flex grows) so it will shrink. No overflow expected. Test at 700px viewport. Optionally hide sparkline on mobile using a media query.
**Warning signs:** Horizontal scrollbar appearing in the 3-col grid on mobile.

### Pitfall 5: Empty State CTA Already Partially Exists
**What goes wrong:** The portfolio card already has a basic empty state at line 234 (`<Link href="/portfolio" className={styles.emptyLink}>Pozisyon ekle</Link>`). Duplicating it creates two elements.
**Why it happens:** DESIGN-06 describes adding a "boş durum" — the skeleton is already there, but it's a single link with no description text or icon.
**How to avoid:** Replace the existing `<Link>` with the full empty-state block (icon + description + CTA link). Don't add a second element.
**Warning signs:** Two "Pozisyon ekle" links appearing when positions = 0.

---

## Code Examples

### DESIGN-01: Period tabs with 1G and 1H added

```tsx
// page.tsx — replace line 105 and lines 191–199
const [chartPeriod, setChartPeriod] = useState<'1G' | '1H' | '1A' | '3A' | '1Y' | 'Tüm'>('1A');

// In JSX:
<div className={styles.periodTabs}>
  {(['1G', '1H', '1A', '3A', '1Y', 'Tüm'] as const).map((p) => (
    <button
      key={p}
      className={`${styles.periodTab} ${chartPeriod === p ? styles.periodTabActive : ''}`}
      onClick={() => setChartPeriod(p)}
    >
      {p}
    </button>
  ))}
</div>
```

### DESIGN-01: Bist100Chart with seed data fallback

```tsx
// Extend Bist100Chart props
function Bist100Chart({
  points,
  color,
  period,
  seedValues,   // <-- new optional prop
}: {
  points: Bist100HistoryResponse['points'];
  color: string;
  period: string;
  seedValues?: number[];
}) {
  const visiblePoints = useMemo(() => {
    if ((period === '1G' || period === '1H') && seedValues) return null; // use seedValues path
    const n = period === '1A' ? 30 : period === '3A' ? 90 : period === '1Y' ? 252 : points.length;
    return points.slice(-n);
  }, [period, points, seedValues]);

  const values = visiblePoints
    ? visiblePoints.map((p) => p.close)
    : (seedValues ?? []);
  // rest of chart rendering is identical
```

### DESIGN-04: Hover fix (single line change)

```css
/* page.module.css line 373 — change: */
.stockRow:hover { background: rgba(255, 255, 255, 0.03); }
/* to: */
.stockRow:hover { background: var(--bg-elevated); }
```

`--bg-elevated` is `#1c1f24` in dark mode and `#f4f4f5` in light mode (confirmed from globals.css lines 16 and 100 respectively). Both are visually correct hover colors in their respective themes.

### DESIGN-06: Portfolio empty state block

```tsx
{/* Replace the existing single <Link> with: */}
<div className={styles.portfolioEmpty}>
  <p className={styles.portfolioEmptyText}>Henüz portföy pozisyonu eklenmedi.</p>
  <Link href="/portfolio" className={styles.emptyLink}>Pozisyon ekle →</Link>
</div>
```

Add to `page.module.css`:
```css
.portfolioEmpty {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 8px;
}

.portfolioEmptyText {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.5;
}
```

---

## Exact File Audit

### frontend/src/app/page.tsx (DESIGN-01, DESIGN-02, DESIGN-06)

| Line | Current state | Required change |
|------|--------------|-----------------|
| 105 | `useState<'1A' \| '3A' \| '1Y' \| 'Tüm'>` | Add `'1G' \| '1H'` to union |
| 191 | Array `['1A', '3A', '1Y', 'Tüm']` | Add `'1G'` and `'1H'` at front |
| 34 | `n =` ternary with 4 cases | Add 1G/1H → use seed path |
| 204 | `<Bist100Chart points={...}` | Pass `seedValues` when period is 1G/1H |
| 338–359 | `StockRows` renders 4 grid columns | Add `<MiniSparkline>` as 5th child; widen grid |
| 234 | Single `<Link>Pozisyon ekle</Link>` | Wrap in `portfolioEmpty` div, add description text |
| (new) | No `seedSeries()` function | Add deterministic LCG seed function |
| (new) | No `MiniSparkline` component | Add inline SVG sparkline sub-component |

### frontend/src/app/page.module.css (DESIGN-04)

| Line | Current | Fix |
|------|---------|-----|
| 373 | `.stockRow:hover { background: rgba(255, 255, 255, 0.03); }` | Change to `var(--bg-elevated)` |
| (new) | No `.portfolioEmpty` / `.portfolioEmptyText` | Add styles for DESIGN-06 empty state |
| 360 | `grid-template-columns: 52px 1fr 68px 68px` | Add sparkline column: `52px 1fr 40px 68px 68px` |

### frontend/src/app/model-portfolio/page.tsx (DESIGN-03)

| Current | Change |
|---------|--------|
| 155 lines, only `AiPortfolioSection` | Add `STRATEGIES` constant (6 entries) and `StrategyCards` section below `AiPortfolioSection` |
| No static card rendering | Add grid of 6 `<div className={styles.strategyCard}>` elements |

### frontend/src/app/model-portfolio/page.module.css (DESIGN-03)

| Current | Change |
|---------|--------|
| No strategy card CSS | Add `.strategyGrid`, `.strategyCard`, `.strategyIcon`, `.strategyName`, `.strategyDesc`, `.strategyBadge` |

### frontend/src/components/SparklineWidget.tsx (DESIGN-05)

**Action: DELETE entire file.** Confirmed zero imports anywhere in `frontend/src/app/` or `frontend/src/components/` (only self-defines + imports `SparklinePoint` from api.ts).

### frontend/src/lib/api.ts (DESIGN-05)

**Dead methods to remove** (lines 870–884):
- `getSourceCatalog` (line 870–872)
- `getSourceHealthHistory` (lines 873–879)
- `scanSource` (lines 880–884)

**Orphan interfaces to remove** (in dependency order):
- `SourceHealthAlertItem` (lines 170–177)
- `SourceHealthHistoryItem` (lines 153–161)
- `SourceCatalogItem` (lines 117–131)
- `SourceCatalogResponse` (lines 133–151)
- `SourceHealthHistoryResponse` (lines 162–169)
- `SourceHealthRollupItem` (lines 179–189)
- `SourceHealthDashboardResponse` (lines 191–216)
- `SparklinePoint` (lines 649–652) — only used in SparklineWidget.tsx (being deleted) and `SparklineResponse`
- `SparklineResponse` (lines 654–657) — only used in SparklineWidget.tsx

**Keep intact** (other types used in active pages):
- `HealthResponse`, `HealthSourceStatus` — referenced in at least one active component
- All Market*, Portfolio*, ModelPortfolio*, Intelligence*, StockSummary interfaces — actively used in multiple pages

---

## Validation Architecture

nyquist_validation is enabled (`config.json`). This phase is frontend-only (no backend changes). The project has no frontend test framework (no jest.config, no vitest.config, no `__tests__` directory in frontend). Backend pytest exists but is irrelevant for pure frontend CSS/TSX changes.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | None detected for frontend (ESLint + TypeScript type-check only) |
| Config file | `frontend/tsconfig.json` (strict mode), `frontend/eslint.config.mjs` |
| Quick run command | `cd frontend && npx tsc --noEmit` |
| Full suite command | `cd frontend && npx tsc --noEmit && npx next build` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DESIGN-01 | chartPeriod type includes '1G', '1H'; tabs render 6 buttons | TypeScript type-check | `npx tsc --noEmit` | ✅ tsconfig.json |
| DESIGN-02 | MiniSparkline renders in StockRows | TypeScript type-check | `npx tsc --noEmit` | ✅ tsconfig.json |
| DESIGN-03 | 6 strategy cards rendered as static JSX | TypeScript type-check | `npx tsc --noEmit` | ✅ tsconfig.json |
| DESIGN-04 | CSS uses var(--bg-elevated) not hardcoded rgba | manual-only (CSS visual) | n/a — visual in browser | manual |
| DESIGN-05 | SparklineWidget.tsx gone; dead api methods gone | TypeScript type-check (no broken imports) | `npx tsc --noEmit` | ✅ tsconfig.json |
| DESIGN-06 | Portfolio card empty state has CTA + description | TypeScript type-check | `npx tsc --noEmit` | ✅ tsconfig.json |

### Sampling Rate

- **Per task commit:** `cd frontend && npx tsc --noEmit`
- **Per wave merge:** `cd frontend && npx tsc --noEmit && npx next build`
- **Phase gate:** Build green + manual visual check in both light and dark mode before `/gsd:verify-work`

### Wave 0 Gaps

None — no test files to create. TypeScript strict mode via tsconfig.json is the automated gate. ESLint is available via `npx next lint`.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| lightweight-charts for sparklines | Inline SVG polyline | Bist100Chart already uses SVG in current code | SparklineWidget is obsolete for this use case |
| Hardcoded rgba hover | CSS custom property `var(--bg-elevated)` | Phase 34 fix | Theme-agnostic hover in both dark and light mode |

**Deprecated/outdated:**
- `SparklineWidget.tsx`: Uses `lightweight-charts` (heavy dep, async import) for a 60px tall sparkline. The same visual can be achieved with 10 lines of inline SVG. The component was never imported after it was built.

---

## Open Questions

1. **seedSeries base value for 1G/1H**
   - What we know: `bist100?.value` is the latest BIST100 index value (could be ~9000–12000)
   - What's unclear: Should the mock data be centered on the latest close or an arbitrary constant?
   - Recommendation: Use `bist100?.value ?? 9000` as `base` and `spread = 200` (roughly ±2%). This gives a plausible short-term chart without implying actual intraday data.

2. **Strategy cards: link or static?**
   - What we know: The roadmap has no active strategy-detail page yet (that is Phase 39 territory)
   - What's unclear: Should the cards be clickable (to /model-portfolio/temettü etc.)?
   - Recommendation: Render as non-clickable `<div>` elements for now. Add `cursor: pointer` only if a hover state is wanted; no `<Link>` since there's no destination page. This matches DESIGN-03 wording: "statik kartlar, API gerekmez."

---

## Sources

### Primary (HIGH confidence — direct file inspection)

- `frontend/src/app/page.tsx` — full file read; chartPeriod state, StockRows, portfolio card, Bist100Chart confirmed
- `frontend/src/app/page.module.css` — full file read; hardcoded rgba at line 373 confirmed; stockRow grid columns confirmed
- `frontend/src/app/model-portfolio/page.tsx` — full file read; 155 lines, 0 strategy cards confirmed
- `frontend/src/app/model-portfolio/page.module.css` — full file read; no strategy card CSS confirmed
- `frontend/src/components/SparklineWidget.tsx` — full file read; only self-imports confirmed
- `frontend/src/lib/api.ts` — full file read; 3 dead methods (lines 870–884) confirmed; 9 orphan interfaces confirmed; SparklinePoint only used in SparklineWidget
- `frontend/src/app/globals.css` — full file read; `--bg-elevated: #1c1f24` (dark) and `--bg-elevated: #f4f4f5` (light) confirmed
- `grep -rn "SparklineWidget"` — zero imports in app/ and components/ confirmed
- `grep -rn "getSourceCatalog\|scanSource\|getSourceHealthHistory"` — only in api.ts, zero consumer pages confirmed

### Secondary (MEDIUM confidence)

- `.planning/REQUIREMENTS.md` — DESIGN-01..06 requirements read directly
- `.planning/ROADMAP.md` — Plan split 34-01 / 34-02 confirmed
- `.planning/config.json` — nyquist_validation: true confirmed

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already installed, no new deps
- Architecture: HIGH — all patterns sourced from existing code in the repo
- Pitfalls: HIGH — identified from direct line-by-line inspection

**Research date:** 2026-05-08
**Valid until:** 2026-06-07 (30 days; stable Next.js/CSS project)
