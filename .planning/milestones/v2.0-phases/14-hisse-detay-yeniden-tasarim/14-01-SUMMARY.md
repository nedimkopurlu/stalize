---
phase: 14-hisse-detay-yeniden-tasarim
plan: "01"
subsystem: frontend/stock-detail
tags: [glassmorphism, layout, refactor, ui]
dependency_graph:
  requires: []
  provides: [stock-detail-glassmorphism-layout, tab-removed, causal-removed]
  affects: [frontend/src/app/stocks/[symbol]/page.tsx, frontend/src/app/stocks/[symbol]/stock.module.css]
tech_stack:
  added: []
  patterns: [glassmorphism-card, vertical-layout, backdrop-filter]
key_files:
  created: []
  modified:
    - frontend/src/app/stocks/[symbol]/page.tsx
    - frontend/src/app/stocks/[symbol]/stock.module.css
decisions:
  - Sidebar layout replaced with full-width vertical stack — chart, metrics, signals+KAP all in sequence
  - KAP news moved from sidebar into bottomGrid right column (real data wired, not placeholder)
  - Temel Bilgiler infoGrid kept at bottom in glassCard (not removed)
  - sectionTitle updated to uppercase label style consistent with glassmorphism context
metrics:
  duration: "~20 minutes"
  completed: "2026-04-26"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 2
---

# Phase 14 Plan 01: Hisse Detay Sayfası Glassmorphism Layout Yeniden Tasarım

Hisse detay sayfası tab sistemi kaldırılarak yeniden yazıldı: activeTab state, tab-bar ve tüm chart/technical tab mantığı silindi; dikey glassmorphism layout uygulandı — tam genişlikte fiyat grafiği üstte, 2-sütun metrik kartları ortada, teknik sinyaller ve KAP bildirimleri altta.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Causal tab sil, glassmorphism layout yaz | b308d13a | frontend/src/app/stocks/[symbol]/page.tsx |
| 2 | Glassmorphism layout stilleri — stock.module.css | ee423cc5 | frontend/src/app/stocks/[symbol]/stock.module.css |

## What Was Built

### New Layout Structure

1. **Header** — TerminalPageHeader + breadcrumb korundu
2. **ScoreLayerPanel** — 3-katman skor paneli korundu
3. **ScoreBreakdown** — skor bileşen kartları korundu
4. **Chart Section** (full-width glassCard) — CandlestickPanel + period bar, tab olmadan
5. **Metrics Row** (2-sütun glassCard'lar) — Temel Metrikler placeholder + Risk Seviyeleri (stop-loss, hedef, destek, direnç)
6. **Bottom Grid** (2-sütun) — Teknik Sinyaller (sol) + Son KAP Bildirimleri (sag)
7. **Temel Bilgiler** (full-width glassCard, alt) — piyasa değeri, hacim, sektör, para birimi

### Removed

- `activeTab` state ve tab switching mantığı
- `.tabBar` tab-bar render
- Sidebar (`workspaceGrid` + `sideDossier`) layout
- `workspaceGrid` ve `primaryWorkspace` class kullanımı

### New CSS Classes

- `.glassCard` — `backdrop-filter: blur(16px)`, `rgba(17,24,39,0.6)` background, `rgba(148,163,184,0.10)` border, 16px radius
- `.metricsRow` — 2-column grid, responsive 1-col at 768px
- `.bottomGrid` — 2-column grid for signals+KAP, responsive
- `.sectionTitle` — updated to uppercase 0.75rem label style

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written with one minor addition:

**1. [Rule 2 - Missing Content] Risk seviyeleri kartı genişletildi**
- **Found during:** Task 1
- **Issue:** Plan sadece stop_loss ve target_price gösteriyordu; destek/direnç verileri teknik objeden mevcut ama gösterilmiyordu
- **Fix:** Risk Seviyeleri kartına destek ve direnç satırları eklendi (zaten technical state'ten mevcut)
- **Files modified:** frontend/src/app/stocks/[symbol]/page.tsx
- **Commit:** b308d13a

**2. [Rule 2 - Missing Content] KAP bildirimleri placeholder yerine gerçek data wired**
- **Found during:** Task 1
- **Issue:** Plan "Yükleniyor..." placeholder önerdi; ancak `stockNews` state zaten mevcut ve dolu
- **Fix:** stockNews varsa gerçek haberler, yoksa placeholder gösterilecek şekilde conditional render uygulandı
- **Files modified:** frontend/src/app/stocks/[symbol]/page.tsx
- **Commit:** b308d13a

## Known Stubs

- **Temel Metrikler card** (`page.tsx` ~147. satır): `<p>Yükleniyor...</p>` — Plan 03'te FundamentalMetricCard bileşeniyle doldurulacak (CLEN-02)
- **KAP Bildirimleri** — stockNews boşsa `<p>Yükleniyor...</p>` gösterilir — Plan 03'te KAPNewsCard ile geliştirilecek

Bu stubs intentional: mevcut sayfada KAP bildirimleri zaten gerçek data ile gösteriliyor. FundamentalMetricCard bileşeni henüz mevcut değil (Plan 03 oluşturacak).

## Verification Results

```
# Causal/Nedensellik cleanup
grep -r "causal|Nedensellik|activeTab.*causal" frontend/src/app/stocks/ | wc -l
→ 0 (PASS)

# activeTab removal
grep -c "activeTab" frontend/src/app/stocks/[symbol]/page.tsx
→ 0 (PASS)

# CSS class presence
grep -c "glassCard|metricsRow|bottomGrid" stock.module.css
→ 5 (PASS)

# TypeScript compilation
npx tsc --noEmit (excluding pre-existing .next/dev/types/app/causal error)
→ 0 new errors (PASS)
```

## Self-Check: PASSED

- frontend/src/app/stocks/[symbol]/page.tsx — FOUND, 260 lines
- frontend/src/app/stocks/[symbol]/stock.module.css — FOUND, glassmorphism classes present
- Commit b308d13a — FOUND
- Commit ee423cc5 — FOUND
