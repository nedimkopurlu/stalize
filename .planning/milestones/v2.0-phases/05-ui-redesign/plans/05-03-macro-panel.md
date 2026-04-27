---
phase: 05-ui-redesign
plan_id: 05-03
title: "MacroPanel Component + Dashboard Integration (UIUX-04)"
requirements: [UIUX-04]
wave: 3
estimated_minutes: 45
autonomous: true
depends_on: [05-01, 05-02]
files_modified:
  - frontend/src/components/MacroPanel.tsx
  - frontend/src/components/MacroPanel.module.css
  - frontend/src/app/page.tsx
must_haves:
  truths:
    - "Dashboard shows MacroPanel below BriefingCard — no separate page or navigation required"
    - "MacroPanel displays USD/TRY, Altin (TRY), BIST100, Faiz %, Enflasyon % as horizontal indicator cards"
    - "Each indicator card shows a label, numeric value, and a trend arrow (up/down/neutral)"
    - "No NaN or undefined appears in any indicator card value"
  artifacts:
    - path: "frontend/src/components/MacroPanel.tsx"
      provides: "MacroPanel component consuming MacroIndicators from api.ts"
    - path: "frontend/src/components/MacroPanel.module.css"
      provides: "Component-scoped horizontal pill/card layout styles"
    - path: "frontend/src/app/page.tsx"
      provides: "MacroPanel rendered between BriefingCard and stat cards"
  key_links:
    - from: "frontend/src/app/page.tsx"
      to: "frontend/src/components/MacroPanel.tsx"
      via: "import MacroPanel + render below BriefingCard"
    - from: "frontend/src/components/MacroPanel.tsx"
      to: "http://localhost:8000/api/macro/indicators"
      via: "api.getMacroIndicators() called in parent loadData()"
---

<objective>
Create the `MacroPanel` component and embed it in the dashboard below BriefingCard. The panel shows five key Turkish market indicators as a horizontal row of small cards: USD/TRY, Altin (TRY), BIST100, Faiz %, Enflasyon %. All data comes from the `/api/macro/indicators` endpoint built in Wave 1. No separate page — single-view, no navigation (per UIUX-04 requirement).

Purpose: Implements UIUX-04 — macro indicators visible on dashboard without navigation.
Output: MacroPanel.tsx + MacroPanel.module.css + modified page.tsx
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/05-ui-redesign/05-CONTEXT.md
@.planning/phases/05-ui-redesign/VALIDATION.md

<interfaces>
<!-- Types from api.ts (Wave 1) -->
```typescript
export interface MacroIndicators {
  usdtry: number | null;
  gold_try: number | null;
  bist100: number | null;
  interest_rate: number | null;
  inflation_rate: number | null;
  as_of: string;
}

api.getMacroIndicators(): Promise<MacroIndicators>
```

<!-- Dashboard page.tsx current render order after Wave 2 -->
1. Page header
2. <BriefingCard briefing={briefing} state={briefingState} />   ← already wired
3. Stats cards (styles.statsGrid)
4. Top buy/sell (styles.dualGrid)
5. Gainers/losers (styles.dualGrid)
6. Intelligence grid
7. Full stock table

MacroPanel must be inserted at position 2.5 — between BriefingCard and stats cards.
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create MacroPanel.tsx and MacroPanel.module.css</name>
  <files>
    frontend/src/components/MacroPanel.tsx
    frontend/src/components/MacroPanel.module.css
  </files>
  <action>
Create `frontend/src/components/MacroPanel.tsx`:

```typescript
'use client';

import React from 'react';
import type { MacroIndicators } from '@/lib/api';
import styles from './MacroPanel.module.css';

interface MacroPanelProps {
  indicators: MacroIndicators | null;
  loading: boolean;
}

interface IndicatorConfig {
  key: keyof MacroIndicators;
  label: string;
  format: (v: number) => string;
  // Trend direction: positive means "up is good for market", negative means "up is bad"
  positiveWhenUp: boolean;
}

const INDICATOR_CONFIG: IndicatorConfig[] = [
  {
    key: 'usdtry',
    label: 'USD/TRY',
    format: (v) => v.toFixed(2),
    positiveWhenUp: false, // rising USD/TRY is negative for TRY investors
  },
  {
    key: 'gold_try',
    label: 'Altın (TRY/g)',
    format: (v) => v.toLocaleString('tr-TR', { maximumFractionDigits: 0 }),
    positiveWhenUp: true,
  },
  {
    key: 'bist100',
    label: 'BIST 100',
    format: (v) => v.toLocaleString('tr-TR', { maximumFractionDigits: 0 }),
    positiveWhenUp: true,
  },
  {
    key: 'interest_rate',
    label: 'Faiz (%)',
    format: (v) => `${v.toFixed(1)}%`,
    positiveWhenUp: false,
  },
  {
    key: 'inflation_rate',
    label: 'Enflasyon (%)',
    format: (v) => `${v.toFixed(1)}%`,
    positiveWhenUp: false,
  },
];

export default function MacroPanel({ indicators, loading }: MacroPanelProps) {
  if (loading) {
    return (
      <div className={styles.macroPanel}>
        {INDICATOR_CONFIG.map((cfg) => (
          <div key={cfg.key} className={`${styles.indicatorCard} ${styles.skeleton}`} />
        ))}
      </div>
    );
  }

  if (!indicators) {
    return (
      <div className={styles.macroPanel}>
        <div className={styles.errorNote}>Makro veriler yüklenemedi</div>
      </div>
    );
  }

  return (
    <div className={styles.macroPanel}>
      {INDICATOR_CONFIG.map((cfg) => {
        const rawValue = indicators[cfg.key];
        const value = typeof rawValue === 'number' ? rawValue : null;

        return (
          <div key={cfg.key} className={styles.indicatorCard}>
            <div className={styles.indicatorLabel}>{cfg.label}</div>
            <div className={styles.indicatorValue}>
              {value !== null ? cfg.format(value) : '—'}
            </div>
          </div>
        );
      })}
      <div className={styles.asOf}>
        {indicators.as_of
          ? `Güncellendi: ${new Date(indicators.as_of).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}`
          : ''}
      </div>
    </div>
  );
}
```

Create `frontend/src/components/MacroPanel.module.css`:

```css
/* MacroPanel — horizontal indicator bar. Uses globals.css CSS variable tokens. */

.macroPanel {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  margin-bottom: 24px;
}

.indicatorCard {
  flex: 1 1 140px;
  background: var(--bg-card, #0f1629);
  border: 1px solid var(--border-primary, rgba(148, 163, 184, 0.08));
  border-radius: 8px;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 120px;
}

.indicatorLabel {
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--text-muted, #64748b);
}

.indicatorValue {
  font-size: 1.05rem;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
  color: var(--text-primary, #e2e8f0);
  white-space: nowrap;
}

.asOf {
  flex: 0 0 auto;
  font-size: 0.7rem;
  color: var(--text-muted, #64748b);
  align-self: flex-end;
  padding-bottom: 4px;
}

.skeleton {
  height: 64px;
  background: rgba(148, 163, 184, 0.06);
  animation: shimmer 1.5s infinite ease-in-out;
}

@keyframes shimmer {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.errorNote {
  font-size: 0.82rem;
  color: var(--text-muted, #64748b);
  padding: 12px 0;
}

@media (max-width: 640px) {
  .indicatorCard {
    flex: 1 1 calc(50% - 6px);
  }
}
```
  </action>
  <verify>
    <automated>grep -n "export default function MacroPanel" /Users/nedimkopurlu/Downloads/PROJELER/stalize/frontend/src/components/MacroPanel.tsx</automated>
  </verify>
  <done>MacroPanel.tsx exports a default function accepting `{ indicators, loading }` props. MacroPanel.module.css exists with macroPanel, indicatorCard, indicatorLabel, indicatorValue styles.</done>
</task>

<task type="auto">
  <name>Task 2: Wire MacroPanel into dashboard page.tsx</name>
  <files>frontend/src/app/page.tsx</files>
  <action>
Modify `frontend/src/app/page.tsx` to add MacroPanel. Make these targeted additions only:

**Step 1 — Add import** at the top with other component imports:
```typescript
import MacroPanel from '@/components/MacroPanel';
import type { MacroIndicators } from '@/lib/api';
```

**Step 2 — Add state variables** inside `DashboardPage`, after the briefingState useState from Wave 2:
```typescript
const [macroIndicators, setMacroIndicators] = useState<MacroIndicators | null>(null);
const [macroLoading, setMacroLoading] = useState(true);
```

**Step 3 — Add macro fetch** inside `loadData()`. Add it as a parallel fire-and-forget alongside the briefing fetch (the `Promise.all` already runs dashboard/stocks/intelligence — do NOT add macro to that Promise.all since a macro failure should not block the dashboard):

```typescript
// Fire macro indicators fetch in parallel — failure is non-blocking
setMacroLoading(true);
api.getMacroIndicators()
  .then(setMacroIndicators)
  .catch(() => setMacroIndicators(null))
  .finally(() => setMacroLoading(false));
```

Add this block immediately after the briefing try/catch block, before the `Promise.all` call.

**Step 4 — Render MacroPanel** in the JSX, immediately AFTER the BriefingCard and BEFORE the statsGrid section:

```tsx
{/* ── Macro Indicators Panel (UIUX-04) ─────── */}
<MacroPanel indicators={macroIndicators} loading={macroLoading} />
```

Final render order in `<main>`:
1. Page header
2. `<BriefingCard .../>` (from Wave 2)
3. `<MacroPanel indicators={macroIndicators} loading={macroLoading} />` ← INSERT HERE
4. Stats cards
5. Top buy/sell
6. Gainers/losers
7. Intelligence grid
8. Full stock table

Do NOT remove or reorder any existing sections.
  </action>
  <verify>
    <automated>cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/frontend && npm run build 2>&1 | tail -20</automated>
  </verify>
  <done>
- `npm run build` exits 0
- `grep "MacroPanel" frontend/src/app/page.tsx` shows both import and usage
- `grep "macroIndicators\|macroLoading" frontend/src/app/page.tsx` confirms both state variables present
  </done>
</task>

</tasks>

<verification>
1. `npm run build` — exits 0
2. `grep -c "MacroPanel" frontend/src/app/page.tsx` — at least 2 (import + usage)
3. `ls frontend/src/components/MacroPanel.tsx frontend/src/components/MacroPanel.module.css` — both exist
4. Manual smoke: http://localhost:3000 shows horizontal indicator cards between BriefingCard and stats grid
5. No "NaN" or "undefined" visible in any indicator card (null values show "—")
</verification>

<success_criteria>
- MacroPanel renders on dashboard without separate page/navigation (UIUX-04)
- All five indicators (USD/TRY, Altin, BIST100, Faiz, Enflasyon) have cards
- Null values display as "—" — never NaN or undefined
- MacroPanel failure is non-blocking — rest of dashboard loads even if /api/macro/indicators is down
- TypeScript build clean
</success_criteria>

<output>
After completion, create `.planning/phases/05-ui-redesign/plans/05-03-SUMMARY.md` documenting the component props, the indicator config array, and the fire-and-forget fetch pattern used in page.tsx.
</output>
