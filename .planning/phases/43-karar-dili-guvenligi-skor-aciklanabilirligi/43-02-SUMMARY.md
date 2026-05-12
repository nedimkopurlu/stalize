---
phase: 43
plan: 02
subsystem: frontend
tags: [score-breakdown, data-integrity, volatility-warning, transparency]
dependency_graph:
  requires: [43-01]
  provides: [KARAR-02, KARAR-03, SKOR-01, SKOR-02, SKOR-03]
  affects: [stocks-detail-page, stocks-list-page]
tech_stack:
  added: []
  patterns: [progress-bar-breakdown, component-counter-badge, volatility-proxy]
key_files:
  created: []
  modified:
    - frontend/src/app/stocks/[symbol]/page.tsx
    - frontend/src/app/stocks/[symbol]/page.module.css
    - frontend/src/app/stocks/page.tsx
    - frontend/src/app/stocks/page.module.css
decisions:
  - "Volatilite proxy listede daily_change_pct >%4 (günlük) — 20 günlük fiyat geçmişi hisse listesinde mevcut değil"
  - "Skor Dökümü bölümü hero section'dan sonra ayrı <section> olarak eklendi — scoreCard içinde değil"
  - "componentIntegrity scoreCard içinde scoreBars altına konuldu — scoreCard ile bütünleşik görünüm"
metrics:
  duration: "~10 dakika"
  completed: "2026-05-12"
  tasks_completed: 2
  files_modified: 4
---

# Phase 43 Plan 02: Skor Dökümü & Veri Bütünlüğü Göstergesi Summary

**One-liner:** Hisse detayda progress bar formatında skor bileşen dökümü + her iki sayfada N/3 bileşen sayacı ve volatilite uyarısı eklendi.

## What Was Built

### Task 1: Skor Dökümü (hisse detay)
- `volatilityAlert`: Son 20 günlük kapanış fiyatı değişimi >%15 ise `true` döndüren hesaplama
- `totalComponentCount` / `availableComponentCount`: `bd.summary` üzerinden bileşen sayaçları
- `componentIntegrity` div: scoreCard'ın scoreBars bölümü altında N/N bileşen mevcut + volatilite uyarısı
- `breakdownSection`: Yeni `<section>` — her bileşen için renk kodlu progress bar + katkı yüzdesi + neden tooltip
- Eksik bileşen varsa amber uyarı kutusu: "Eksik veri — ağırlık yeniden dağıtıldı"
- CSS: `breakdownSection`, `breakdownBar*`, `componentIntegrity`, `volatilityWarning`

### Task 2: Veri Bütünlüğü (hisse listesi)
- `componentCount(stock)`: fundamental/technical/sentiment_score üzerinden available/total hesaplar
- `isHighDailyVolatility(stock)`: `daily_change_pct > %4` proxy (20g fiyat geçmişi listede yok)
- F/K sütunundaki hücre güncellendi: fundamental_score + componentBadge + volWarn ikonu
- `componentBadge[data-incomplete]`: eksik bileşende amber renk + özel border
- CSS: `integrityCell`, `componentBadge`, `volWarn`

## Commits

| Task | Commit | Files |
|------|--------|-------|
| Task 1: Skor Dökümü + volatilite | `00e8a23` | stocks/[symbol]/page.tsx, page.module.css |
| Task 2: Hisse listesi veri bütünlüğü | `a08c526` | stocks/page.tsx, stocks/page.module.css |

## Deviations from Plan

None — plan exactly as written.

## Known Stubs

None — all data wired to live API responses (`bd.components`, `bd.summary`, `stock.fundamental_score` etc).

## Self-Check: PASSED

- `frontend/src/app/stocks/[symbol]/page.tsx` — modified, exists
- `frontend/src/app/stocks/[symbol]/page.module.css` — modified, exists
- `frontend/src/app/stocks/page.tsx` — modified, exists
- `frontend/src/app/stocks/page.module.css` — modified, exists
- Commits `00e8a23` and `a08c526` exist in git log
- TypeScript build passes (no errors)
