---
phase: 54-backtest-kalitesi
plan: "02"
subsystem: frontend
tags: [backtest, regime, slippage, api-types, typescript]
dependency_graph:
  requires: [54-01]
  provides: [regime-filter-ui, regime-breakdown-table, slippage-kpi-card]
  affects: [frontend/src/app/backtest/page.tsx, frontend/src/lib/api.ts]
tech_stack:
  added: []
  patterns: [regime-filter-state, conditional-table-render, optional-api-param]
key_files:
  created: []
  modified:
    - frontend/src/lib/api.ts
    - frontend/src/app/backtest/page.tsx
    - frontend/src/app/backtest/backtest.module.css
decisions:
  - "ASCII-safe CSS class names used (regimeBoga/Ayi instead of regimeBoğa/Ayı) to avoid CSS module key lookup issues"
  - "Regime label mapping via explicit if/else chain in JSX for type safety instead of dynamic bracket access"
  - "regimeFilter drives both outcomes and calibration API calls so all data (table + KPIs) stays in sync"
metrics:
  duration: "~10 minutes"
  completed: "2026-05-15T17:20:42Z"
  tasks_completed: 2
  files_modified: 3
---

# Phase 54 Plan 02: Backtest Rejim Kırılımı ve Slipaj KPI — Frontend Summary

**One-liner:** Backtest sayfasına rejim filtre dropdown, rejim bazlı performans tablosu ve slipaj maliyeti KPI kartı eklendi; api.ts yeni `by_regime`/`by_slippage_cost` type alanları ve opsiyonel `regime` parametreli API metodları içeriyor.

## What Was Built

### Task 1 — api.ts Type Güncellemeleri (commit: 13069a0)

- `SignalOutcomeItem` interface'ine `regime: string | null` eklendi
- `SignalCalibrationResponse` interface'ine iki yeni alan eklendi:
  - `by_regime: SignalCalibrationBucket[]` — plan 54-01'den gelen rejim kırılım verisi
  - `by_slippage_cost: { assumed_round_trip_cost_pct, gross_avg_return_pct, net_avg_return_pct, note } | null`
- `getSignalOutcomes(limit, horizon, regime?)` — opsiyonel `regime` parametresi eklendi
- `getSignalCalibration(horizon, minCount, regime?)` — opsiyonel `regime` parametresi eklendi
- Her iki metod `encodeURIComponent(regime)` ile URL-safe parametre ekler

### Task 2 — Backtest Sayfası UI (commit: 97faa99)

**Yeni state:** `const [regimeFilter, setRegimeFilter] = useState('')`

**REGIME_OPTIONS sabiti:**
```typescript
[
  { label: 'Tüm Rejimler', value: '' },
  { label: 'Boğa', value: 'Boğa' },
  { label: 'Ayı', value: 'Ayı' },
  { label: 'Yatay', value: 'Yatay' },
  { label: 'Volatil', value: 'Volatil' },
]
```

**loadData() güncellemesi:** Tüm üç API çağrısına `regimeFilter || undefined` iletildi. `useEffect` bağımlılık dizisine `regimeFilter` eklendi.

**Yeni KPI kartı:** "Net Getiri (Maliyet Sonrası)" — `by_slippage_cost.net_avg_return_pct` gösterir; alt metin brüt getiri ve round-trip maliyeti içerir.

**Rejim dropdown:** Filtre bar'da outcomeFilter'dan sonra eklendi; değişimde `regimeFilter` state güncellenir ve useEffect tetiklenir.

**Rejim Bazlı Performans tablosu:** `calibration.by_regime.length > 0` koşulunda render edilir:
- Sütunlar: Rejim | Sinyal | Başarı % | Ort. Getiri | Ort. Relatif
- Her rejim satırı CSS sınıfıyla renk kodlanır
- Başarı % rengi: >=55 yeşil, >=40 amber, <40 kırmızı

**CSS sınıfları eklendi (backtest.module.css):**
- `.regimeSection`, `.sectionTitle`, `.regimeTable`, `.regimeTable th/td`
- `.regimeBoga` (yeşil), `.regimeAyi` (kırmızı), `.regimeYatay` (accent), `.regimeVolatil` (#f59e0b amber), `.regimeBilinmiyor` (muted)

## Verification Results

| Check | Result |
|-------|--------|
| `grep by_regime frontend/src/lib/api.ts` | PASS |
| `grep "regime: string \| null" frontend/src/lib/api.ts` | PASS |
| `grep regimeFilter frontend/src/app/backtest/page.tsx` | PASS |
| `grep by_regime frontend/src/app/backtest/page.tsx` | PASS |
| `grep regimeTable frontend/src/app/backtest/backtest.module.css` | PASS |
| `cd frontend && npx tsc --noEmit` | PASS (0 errors) |
| `npm run lint` | PASS (0 warnings) |

## Deviations from Plan

**1. [Rule 1 - Bug] ASCII-safe CSS class name mapping**
- **Found during:** Task 2
- **Issue:** Dynamic CSS module bracket access `styles[`regime${row.key}`]` fails silently for keys with Turkish characters (Boğa, Ayı) — CSS modules require valid identifier characters
- **Fix:** Used explicit if/else chain mapping `row.key` to ASCII-safe class names (`regimeBoga`, `regimeAyi`) instead of dynamic key lookup
- **Files modified:** `frontend/src/app/backtest/page.tsx`
- **Commit:** 97faa99

## Known Stubs

None — all rendered data sourced from live API response fields.

## Self-Check: PASSED

- `frontend/src/lib/api.ts` — modified, verified by grep
- `frontend/src/app/backtest/page.tsx` — modified, verified by grep
- `frontend/src/app/backtest/backtest.module.css` — modified, verified by grep
- Commit 13069a0 — exists (`git log --oneline | grep 13069a0`)
- Commit 97faa99 — exists (`git log --oneline | grep 97faa99`)
