---
phase: 05-ui-redesign
plan_id: 05-05
title: "Score Table Score-Range Filter + Human Checkpoint (UIUX-03)"
requirements: [UIUX-03]
wave: 5
estimated_minutes: 35
autonomous: false
depends_on: [05-01]
files_modified:
  - frontend/src/app/stocks/page.tsx
must_haves:
  truths:
    - "Min Skor and Max Skor number inputs appear in the filter bar on /stocks"
    - "Typing 70 in Min Skor instantly hides all stocks with overall_score below 70 — no submit button"
    - "Existing recommendation filter (AL/SAT/TUT) still works alongside score range filter"
    - "Both filters compose: recommendation + score range active simultaneously narrows results correctly"
    - "Table shows symbol, overall_score, recommendation, technical_score, fundamental_score, sentiment_score, daily_change_pct columns"
  artifacts:
    - path: "frontend/src/app/stocks/page.tsx"
      provides: "Filterable score table with minScore/maxScore state and composed filter logic"
  key_links:
    - from: "frontend/src/app/stocks/page.tsx minScore/maxScore state"
      to: "filtered stocks array"
      via: "stocks.filter() — frontend-only, no backend change"
---

<objective>
Add score-range filtering (Min/Max Skor number inputs) to the existing `/stocks` score table. The filter is frontend-only — all 100 stocks are already loaded, filtering is instant on input change. The existing recommendation filter is kept and composes with the new score range filter.

Also ensures the table shows temel/teknik/algi score columns (currently only Teknik + Nedensellik columns are shown).

Purpose: Implements UIUX-03 — all BIST100 ranked by overall_score, filterable by score range AND AL/SAT/TUT.
Output: Modified stocks/page.tsx with score range filter + human verification checkpoint.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/05-ui-redesign/05-CONTEXT.md
@.planning/phases/05-ui-redesign/VALIDATION.md

<interfaces>
<!-- Current stocks/page.tsx filter state (from codebase reading) -->
```typescript
// Existing state:
const [stocks, setStocks] = useState<StockSummary[]>([]);
const [sortBy, setSortBy] = useState('overall_score');
const [filterBist30, setFilterBist30] = useState(false);
const [filterRec, setFilterRec] = useState('');  // existing recommendation filter
const [search, setSearch] = useState('');

// Existing useEffectEvent loadStocks: fetches api.getStocks() and sets stocks
// The 'recommendation' filter is passed as a query param to the API — keep this behavior
// Score range filter: frontend-only, applied after data is loaded
```

<!-- StockSummary scores available -->
```typescript
export interface StockSummary {
  overall_score: number | null;
  technical_score: number | null;
  fundamental_score: number | null;
  sentiment_score: number | null;
  recommendation: string | null;
  daily_change_pct: number | null;
  // ...other fields
}
```

<!-- Current table columns (from codebase) -->
// #, Hisse, Fiyat, Degisim, Hacim, P.Degeri, Sektor, Teknik, Nedensellik, Genel, Sinyal
// Add: Temel (fundamental_score), Algi (sentiment_score) columns
// Temel and Algi use <ScoreRing> just like Teknik
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add score range filter inputs and composed filter logic to stocks/page.tsx</name>
  <files>frontend/src/app/stocks/page.tsx</files>
  <action>
Read the current `frontend/src/app/stocks/page.tsx` fully before editing. Then make the following targeted changes:

**Step 1 — Add state variables** for score range, alongside the existing filter states:
```typescript
const [minScore, setMinScore] = useState<number | ''>('');
const [maxScore, setMaxScore] = useState<number | ''>('');
```

**Step 2 — Add filtered derived array** BEFORE the return statement. This replaces the direct use of `stocks` in the table render:

```typescript
const filtered = stocks.filter((s) => {
  if (minScore !== '' && (s.overall_score ?? 0) < minScore) return false;
  if (maxScore !== '' && (s.overall_score ?? 0) > maxScore) return false;
  return true;
});
```

Note: `filterRec` is already passed to `api.getStocks({ recommendation: filterRec })` as a query param — so the recommendation filter runs on the backend and `stocks` is already pre-filtered by recommendation. The score range filter is applied on top of that in `filtered`. This is correct behavior — do NOT move recommendation filtering to the frontend.

**Step 3 — Add Min/Max Skor inputs** to the filter bar JSX. Insert them after the existing recommendation `<select>` and before the BIST30 toggle button:

```tsx
{/* Score range filter (UIUX-03) */}
<div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
  <input
    type="number"
    className="search-input"
    placeholder="Min Skor"
    min={0}
    max={100}
    value={minScore}
    onChange={(e) => setMinScore(e.target.value === '' ? '' : Number(e.target.value))}
    style={{ flex: '0 0 90px', paddingLeft: 12 }}
  />
  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>–</span>
  <input
    type="number"
    className="search-input"
    placeholder="Max Skor"
    min={0}
    max={100}
    value={maxScore}
    onChange={(e) => setMaxScore(e.target.value === '' ? '' : Number(e.target.value))}
    style={{ flex: '0 0 90px', paddingLeft: 12 }}
  />
</div>
```

**Step 4 — Update table to use `filtered` instead of `stocks`** in the tbody map:
- Change `stocks.map((stock, idx) => ...)` to `filtered.map((stock, idx) => ...)`
- Update the results count display: change `{total} hisse bulundu` to `{filtered.length} / {total} hisse` so the user can see how many are shown after filtering

**Step 5 — Add Temel and Algi columns to the table.** In the `<thead>`:
- Add `<th className="hide-mobile">Temel</th>` after the existing `<th>Teknik</th>`
- Add `<th className="hide-mobile">Algi</th>` after the new Temel th

In the `<tbody>` rows, add corresponding cells:
```tsx
<td className="hide-mobile">
  <ScoreRing score={stock.fundamental_score} size={36} strokeWidth={3} />
</td>
<td className="hide-mobile">
  <ScoreRing score={stock.sentiment_score} size={36} strokeWidth={3} />
</td>
```
Insert these cells immediately after the existing Teknik cell and before the Nedensellik cell.

**Step 6 — Ensure sort is stable.** The `sortBy` default is `'overall_score'` and this is passed to `api.getStocks({ sort_by: sortBy })`. This is already correct — no backend change needed. The `filtered` array preserves the backend sort order.
  </action>
  <verify>
    <automated>cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/frontend && npm run build 2>&1 | tail -20</automated>
  </verify>
  <done>
- `npm run build` exits 0
- `grep "minScore\|maxScore\|filtered" frontend/src/app/stocks/page.tsx` shows all three identifiers
- `grep "Min Skor\|Max Skor" frontend/src/app/stocks/page.tsx` shows both input placeholders
- `grep "fundamental_score\|sentiment_score" frontend/src/app/stocks/page.tsx` shows Temel/Algi columns added
  </done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>
    All four UIUX requirements are implemented:
    - UIUX-01: BriefingCard as dominant dashboard element (Wave 2)
    - UIUX-02: Candlestick chart + ScoreLayerPanel + Teknik Ozet on stock detail (Wave 4)
    - UIUX-03: Score range filter (Min/Max Skor) on /stocks table (this wave)
    - UIUX-04: MacroPanel inline on dashboard (Wave 3)
  </what-built>
  <how-to-verify>
    Run the backend and frontend dev servers, then verify each requirement:

    **Start servers:**
    ```
    cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && uvicorn app.main:app --reload --port 8000
    cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/frontend && npm run dev
    ```

    **UIUX-01 — Dashboard briefing card:**
    1. Open http://localhost:3000
    2. Confirm BriefingCard is the FIRST content element (before stats grid)
    3. If no briefing generated: see "Sabah brifing henuz uretilmedi" message and schedule hint
    4. If briefing exists: see risk_summary, notable_stocks chips, collapsed KAP section

    **UIUX-04 — Macro panel:**
    5. Below BriefingCard: see 5 horizontal indicator cards — USD/TRY, Altin, BIST100, Faiz %, Enflasyon %
    6. All values are numbers (no NaN, no undefined, no blank)
    7. Confirm: curl http://localhost:8000/api/macro/indicators returns JSON with 5 keys

    **UIUX-03 — Score table filter:**
    8. Open http://localhost:3000/stocks
    9. See "Min Skor" and "Max Skor" inputs in the filter bar
    10. Type 70 in Min Skor — stocks with overall_score below 70 disappear immediately
    11. Clear Min Skor, set filterRec to "AL" — only AL stocks show
    12. With both active (Min Skor=60, filterRec=AL) — only AL stocks with score >= 60 show
    13. Temel and Algi score ring columns are visible in the table

    **UIUX-02 — Stock detail:**
    14. Click any stock to open /stocks/THYAO (or similar)
    15. Candlestick chart renders: green candles for up days, red for down days (NOT a flat line)
    16. Below the chart: "Teknik Ozet" section with up to 3 signals
    17. Above chart/tabs: see ScoreLayerPanel with 4 rings (Genel, Temel, Teknik, Algi)
    18. Navigate AWAY from stock detail and BACK — no JS errors in browser console
  </how-to-verify>
  <resume-signal>Type "approved" if all 18 checks pass. Or describe which checks failed with browser console errors or screenshots.</resume-signal>
</task>

</tasks>

<verification>
Automated:
1. `npm run lint && npm run build` — both exit 0
2. `grep -c "minScore\|maxScore" frontend/src/app/stocks/page.tsx` — 4+ occurrences
3. `grep "fundamental_score" frontend/src/app/stocks/page.tsx` — Temel column present

Human checkpoint:
- All 18 smoke test checks pass as documented above
</verification>

<success_criteria>
- Min/Max Skor inputs filter instantly without submit button (UIUX-03)
- Recommendation + score range filters compose correctly
- Temel (fundamental_score) and Algi (sentiment_score) columns visible in table
- Lint + build clean
- Human checkpoint approved after verifying all four UIUX requirements end-to-end
</success_criteria>

<output>
After completion and checkpoint approval, create `.planning/phases/05-ui-redesign/plans/05-05-SUMMARY.md` documenting the filter logic pattern, column additions, and checkpoint outcome.
</output>
