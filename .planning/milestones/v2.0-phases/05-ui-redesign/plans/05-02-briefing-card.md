---
phase: 05-ui-redesign
plan_id: 05-02
title: "BriefingCard Component + Dashboard Integration (UIUX-01)"
requirements: [UIUX-01]
wave: 2
estimated_minutes: 50
autonomous: true
depends_on: [05-01]
files_modified:
  - frontend/src/components/BriefingCard.tsx
  - frontend/src/components/BriefingCard.module.css
  - frontend/src/app/page.tsx
must_haves:
  truths:
    - "Dashboard opens with BriefingCard as the first visible element"
    - "When briefing not generated (404), a clear Turkish empty-state message is shown — not an error"
    - "When briefing exists (200), card shows risk_summary, notable_stocks list, kap_summary (collapsed)"
    - "Existing intelligence/stocks sections remain below BriefingCard — nothing is removed"
  artifacts:
    - path: "frontend/src/components/BriefingCard.tsx"
      provides: "BriefingCard component with loaded and empty states"
    - path: "frontend/src/components/BriefingCard.module.css"
      provides: "Component-scoped styles using existing CSS variable tokens"
    - path: "frontend/src/app/page.tsx"
      provides: "Dashboard page with BriefingCard at top, existing sections below"
  key_links:
    - from: "frontend/src/app/page.tsx"
      to: "frontend/src/components/BriefingCard.tsx"
      via: "import BriefingCard + render above statsGrid"
    - from: "frontend/src/components/BriefingCard.tsx"
      to: "http://localhost:8000/api/briefing/today"
      via: "api.getBriefing() called in parent page.tsx loadData"
---

<objective>
Create the `BriefingCard` component and wire it into the dashboard as the dominant first element. The card has two states: a rich display of the morning briefing content (200 OK) and a "not yet generated" placeholder with a schedule hint (404). The existing dashboard sections (stats, top stocks, intelligence) remain intact below the card.

Purpose: Implements UIUX-01 — briefing-first dashboard experience.
Output: BriefingCard.tsx + BriefingCard.module.css + modified page.tsx
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/05-ui-redesign/05-CONTEXT.md
@.planning/phases/05-ui-redesign/VALIDATION.md

<interfaces>
<!-- Types available from api.ts after Wave 1 -->
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

// Available in api object:
api.getBriefing(): Promise<BriefingData>
```

From frontend/src/app/page.tsx (existing structure):
- `'use client'` — already a client component
- `loadData()` fetches dashboard, stocks, intelligence in parallel via `Promise.all`
- Renders: statsGrid → dualGrid (top_buy/sell) → dualGrid (gainers/losers) → intelligenceGrid → tableCard
- CSS class names: `styles.statsGrid`, `styles.dualGrid`, etc. (page.module.css)
- Existing imports: `Sidebar`, `ScoreRing`, `RecommendationBadge`, `Link`, `api`, `styles`
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create BriefingCard.tsx and BriefingCard.module.css</name>
  <files>
    frontend/src/components/BriefingCard.tsx
    frontend/src/components/BriefingCard.module.css
  </files>
  <action>
Create `frontend/src/components/BriefingCard.tsx`:

```typescript
'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import type { BriefingData } from '@/lib/api';
import styles from './BriefingCard.module.css';

interface BriefingCardProps {
  briefing: BriefingData | null;
  state: 'loading' | 'not_generated' | 'loaded' | 'error';
}

export default function BriefingCard({ briefing, state }: BriefingCardProps) {
  const [kapExpanded, setKapExpanded] = useState(false);

  if (state === 'loading') {
    return (
      <div className={`card ${styles.briefingCard}`}>
        <div className={styles.skeletonLine} style={{ width: '40%', height: 20, marginBottom: 12 }} />
        <div className={styles.skeletonLine} style={{ width: '80%', height: 16, marginBottom: 8 }} />
        <div className={styles.skeletonLine} style={{ width: '70%', height: 16 }} />
      </div>
    );
  }

  if (state === 'not_generated' || !briefing) {
    return (
      <div className={`card ${styles.briefingCard} ${styles.emptyState}`}>
        <div className={styles.emptyIcon}>
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
        </div>
        <h2 className={styles.emptyTitle}>Sabah brifing henüz üretilmedi</h2>
        <p className={styles.emptyHint}>Her hafta içi 06:30'da otomatik olarak üretilir</p>
      </div>
    );
  }

  const riskSummary = briefing.ai_commentary?.risk_summary;
  const marketOutlook = briefing.ai_commentary?.market_outlook;
  const notableStocks = briefing.notable_stocks ?? [];

  return (
    <div className={`card ${styles.briefingCard}`}>
      {/* Header */}
      <div className={styles.cardHeader}>
        <div className={styles.headerLeft}>
          <span className={styles.briefingBadge}>SABAH BRİFİNG</span>
          <span className={styles.briefingDate}>
            {briefing.date
              ? new Date(briefing.date).toLocaleDateString('tr-TR', {
                  weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
                })
              : '—'}
          </span>
        </div>
        {briefing.generation_duration_ms && (
          <span className={styles.genTime}>
            {(briefing.generation_duration_ms / 1000).toFixed(1)}s
          </span>
        )}
      </div>

      {/* Risk Summary */}
      {riskSummary && (
        <div className={styles.section}>
          <div className={styles.sectionLabel}>Risk Özeti</div>
          <p className={styles.sectionText}>{riskSummary}</p>
        </div>
      )}

      {/* Market Outlook */}
      {marketOutlook && (
        <div className={styles.section}>
          <div className={styles.sectionLabel}>Piyasa Görünümü</div>
          <p className={styles.sectionText}>{marketOutlook}</p>
        </div>
      )}

      {/* Price Summary */}
      {briefing.price_summary && (
        <div className={styles.section}>
          <div className={styles.sectionLabel}>Fiyat Özeti</div>
          <p className={styles.sectionText}>{briefing.price_summary}</p>
        </div>
      )}

      {/* Notable Stocks */}
      {notableStocks.length > 0 && (
        <div className={styles.section}>
          <div className={styles.sectionLabel}>Öne Çıkan Hisseler</div>
          <div className={styles.notableList}>
            {notableStocks.slice(0, 6).map((s) => (
              <Link
                key={s.symbol}
                href={`/stocks/${s.symbol}`}
                className={`${styles.notableChip} ${
                  s.direction === 'up' ? styles.chipUp : s.direction === 'down' ? styles.chipDown : ''
                }`}
              >
                {s.symbol}
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* KAP Summary — collapsible */}
      {briefing.kap_summary && (
        <div className={styles.section}>
          <button
            className={styles.collapseToggle}
            onClick={() => setKapExpanded(!kapExpanded)}
            aria-expanded={kapExpanded}
          >
            <span className={styles.sectionLabel}>KAP Özeti</span>
            <span className={styles.collapseIcon}>{kapExpanded ? '▲' : '▼'}</span>
          </button>
          {kapExpanded && (
            <p className={`${styles.sectionText} ${styles.kapText}`}>{briefing.kap_summary}</p>
          )}
        </div>
      )}
    </div>
  );
}
```

Create `frontend/src/components/BriefingCard.module.css`:

```css
/* BriefingCard — uses existing CSS variable tokens from globals.css */

.briefingCard {
  border-left: 3px solid var(--accent-cyan, #22d3ee);
  margin-bottom: 24px;
}

.cardHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.headerLeft {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.briefingBadge {
  background: rgba(34, 211, 238, 0.12);
  color: var(--accent-cyan, #22d3ee);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  padding: 3px 10px;
  border-radius: 4px;
  border: 1px solid rgba(34, 211, 238, 0.25);
}

.briefingDate {
  font-size: 0.82rem;
  color: var(--text-secondary, #94a3b8);
}

.genTime {
  font-size: 0.75rem;
  color: var(--text-muted, #64748b);
  font-family: 'JetBrains Mono', monospace;
}

/* Sections */
.section {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-primary, rgba(148, 163, 184, 0.08));
}

.section:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.sectionLabel {
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-muted, #64748b);
  margin-bottom: 6px;
}

.sectionText {
  font-size: 0.88rem;
  color: var(--text-primary, #e2e8f0);
  line-height: 1.6;
  margin: 0;
}

.kapText {
  max-height: 120px;
  overflow-y: auto;
}

/* Collapsible toggle */
.collapseToggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  margin-bottom: 0;
}

.collapseIcon {
  font-size: 0.65rem;
  color: var(--text-muted, #64748b);
}

/* Notable stocks chips */
.notableList {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
}

.notableChip {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 0.78rem;
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
  text-decoration: none;
  background: var(--bg-secondary, rgba(148, 163, 184, 0.08));
  color: var(--text-primary, #e2e8f0);
  border: 1px solid var(--border-primary, rgba(148, 163, 184, 0.12));
  transition: background 0.15s;
}

.notableChip:hover {
  background: rgba(148, 163, 184, 0.15);
}

.chipUp {
  color: var(--color-positive, #22c55e);
  border-color: rgba(34, 197, 94, 0.2);
}

.chipDown {
  color: var(--color-negative, #ef4444);
  border-color: rgba(239, 68, 68, 0.2);
}

/* Empty state */
.emptyState {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
  border-left-color: var(--border-primary, rgba(148, 163, 184, 0.12));
}

.emptyIcon {
  color: var(--text-muted, #64748b);
  margin-bottom: 16px;
}

.emptyTitle {
  font-size: 1rem;
  font-weight: 500;
  color: var(--text-secondary, #94a3b8);
  margin: 0 0 8px;
}

.emptyHint {
  font-size: 0.82rem;
  color: var(--text-muted, #64748b);
  margin: 0;
}

/* Skeleton */
.skeletonLine {
  background: var(--bg-secondary, rgba(148, 163, 184, 0.08));
  border-radius: 4px;
  animation: shimmer 1.5s infinite ease-in-out;
}

@keyframes shimmer {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
```
  </action>
  <verify>
    <automated>grep -n "export default function BriefingCard" /Users/nedimkopurlu/Downloads/PROJELER/stalize/frontend/src/components/BriefingCard.tsx</automated>
  </verify>
  <done>BriefingCard.tsx exports a default function accepting `{ briefing, state }` props. BriefingCard.module.css exists with briefingCard, emptyState, and section styles.</done>
</task>

<task type="auto">
  <name>Task 2: Wire BriefingCard into dashboard page.tsx</name>
  <files>frontend/src/app/page.tsx</files>
  <action>
Modify `frontend/src/app/page.tsx` to add BriefingCard at the top of the dashboard. Make the following targeted changes — do NOT rewrite unrelated sections:

**Step 1 — Add import** at the top of the import block:
```typescript
import BriefingCard from '@/components/BriefingCard';
import type { BriefingData } from '@/lib/api';
```

**Step 2 — Add state variables** inside `DashboardPage` function, after the existing `useState` declarations:
```typescript
const [briefing, setBriefing] = useState<BriefingData | null>(null);
const [briefingState, setBriefingState] = useState<'loading' | 'not_generated' | 'loaded' | 'error'>('loading');
```

**Step 3 — Add briefing fetch** inside `loadData()`. The briefing fetch must be SEPARATE from the `Promise.all` because a 404 is expected and must not abort the other fetches. Add this block at the beginning of `loadData()`, before the `Promise.all`:

```typescript
// Fetch briefing separately — 404 is a valid "not yet generated" state
setBriefingState('loading');
try {
  const b = await api.getBriefing();
  setBriefing(b);
  setBriefingState('loaded');
} catch (err) {
  const msg = err instanceof Error ? err.message : '';
  if (msg.includes('Brifing') || msg.includes('404') || msg.includes('henüz')) {
    setBriefingState('not_generated');
  } else {
    setBriefingState('error');
  }
}
```

**Step 4 — Render BriefingCard** inside the return JSX. The BriefingCard must appear IMMEDIATELY after the page header `</div>` and BEFORE the `{/* ── Stats Cards ─── */}` section:

```tsx
{/* ── Morning Briefing Card (UIUX-01) ─────────── */}
<BriefingCard briefing={briefing} state={briefingState} />
```

The final render order in the `<main>` element:
1. Page header
2. `<BriefingCard briefing={briefing} state={briefingState} />`  ← INSERT HERE
3. Stats cards
4. Top buy/sell
5. Gainers/losers
6. Intelligence grid
7. Full stock table

Do NOT remove, move, or modify any of the existing sections (3–7 above). Do NOT change the existing `loadData` Promise.all for dashboard/stocks/intelligence.
  </action>
  <verify>
    <automated>cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/frontend && npm run build 2>&1 | tail -20</automated>
  </verify>
  <done>
- `npm run build` exits 0
- `grep "BriefingCard" frontend/src/app/page.tsx` shows both import and usage
- `grep "briefingState" frontend/src/app/page.tsx` shows state variable and setter
  </done>
</task>

</tasks>

<verification>
1. `npm run build` — exits 0 (TypeScript clean)
2. `grep -n "BriefingCard\|briefingState\|getBriefing" frontend/src/app/page.tsx` — all three present
3. `ls frontend/src/components/BriefingCard.tsx frontend/src/components/BriefingCard.module.css` — both exist
4. Manual smoke: http://localhost:3000 shows BriefingCard before the stats grid
</verification>

<success_criteria>
- BriefingCard renders as the dominant first element on dashboard
- 404 from /api/briefing/today shows the "henüz üretilmedi" empty state (not an error)
- 200 from /api/briefing/today shows risk_summary, notable_stocks, kap_summary (collapsed by default)
- TypeScript build clean
</success_criteria>

<output>
After completion, create `.planning/phases/05-ui-redesign/plans/05-02-SUMMARY.md` documenting the component props interface, CSS class names used, and the exact insertion point in page.tsx.
</output>
