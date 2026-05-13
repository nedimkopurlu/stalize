---
phase: 45-veri-tazeligi-sistem-sagligi
plan: "02"
subsystem: frontend
tags: [veri-tazeligi, stale-banner, ui, ux]
dependency_graph:
  requires: [45-01]
  provides: [VERI-01, VERI-02, VERI-03, VERI-04]
  affects: [frontend/src/app/stocks/page.tsx, frontend/src/app/stocks/[symbol]/page.tsx]
tech_stack:
  added: []
  patterns: [date-comparison, conditional-render, css-modules]
key_files:
  created: []
  modified:
    - frontend/src/app/stocks/page.tsx
    - frontend/src/app/stocks/page.module.css
    - frontend/src/app/stocks/[symbol]/page.tsx
    - frontend/src/app/stocks/[symbol]/page.module.css
decisions:
  - "latestUpdate Math.max tüm hisse updated_at'larından hesaplanır; tek bir global zaman damgası"
  - "isStale eşiği 8 saat; piyasa kapandıktan sonraki geceler için uygundur"
  - "analysisDate generated_at yoksa Date.now() fallback kullanır"
  - "periodBadge vendor-data-missing string'i için gizlenir; null için de gizlenir"
metrics:
  duration: "~8 dakika"
  completed: "2026-05-14"
  tasks_completed: 2
  files_modified: 4
---

# Phase 45 Plan 02: Veri Tazeliği UI — Stale Banner, Altbilgi, Period Badge, Analiz Tarihi

**One-liner:** Hisse listesine stale-data uyarı banner + güncelleme saati altbilgisi; hisse detayına fundamental dönem etiketi ve AI analiz tarihi notu eklendi.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Hisse listesi — stale banner ve altbilgi | 8c54922 | stocks/page.tsx, stocks/page.module.css |
| 2 | Hisse detay — fundamental period badge ve AI analiz tarih notu | 7017f5f | stocks/[symbol]/page.tsx, stocks/[symbol]/page.module.css |

## What Was Built

### Task 1: Stale Banner ve Altbilgi (VERI-01, VERI-03)

- `isStale(date)`: 8 saat eşiği; `formatUpdateTime(date)`: `tr-TR` locale ile HH:MM formatı
- `latestUpdate` state: `Math.max(...dates)` ile tüm hisselerin `updated_at` alanından en son tarih
- **Stale banner**: `!loading && isStale(latestUpdate)` koşulunda sarı uyarı kutusu gösterir
- **Altbilgi**: `!loading && latestUpdate !== null` koşulunda "Son güncelleme: HH:MM" metnini tablo altında sağa hizalı gösterir
- CSS: `.staleBanner` (amber 8, border, border-radius 8px), `.tableFooter` (text-dim, right-align)

### Task 2: Period Badge ve Analiz Tarihi (VERI-02, VERI-04)

- `analysisDate` state: `handleAnalyze` içinde `result.generated_at`'ı DD.MM.YYYY formatına çevirir
- AI analiz panelinde `<p className={styles.analysisDate}>Bu analiz {analysisDate} verisine dayanmaktadır.</p>`
- Fundamental section header: `sectionEyebrow` içine `periodBadge` span eklendi; `null` ve `vendor-data-missing` için gizlenir
- CSS: `.analysisDate` (italic, text-dim, 0.72rem), `.periodBadge` (amber border, 0.65rem, inline-block)

## Decisions Made

- `latestUpdate` Math.max ile hesaplanır — sunucuda tek bir "son güncelleme" alanı yok, client-side aggregation uygun
- 8 saat eşiği — Türkiye piyasası 09:00-18:00 EEST; gece/hafta sonu için uygun eşik
- `analysisDate` state'de string tutulur — format dönüşümü render yerine set anında yapılır
- `vendor-data-missing` string kontrolü — bu değer boş period göstermemeli, null gibi davranmalı

## Deviations from Plan

None — plan exactly executed as written.

## Self-Check: PASSED

- `frontend/src/app/stocks/page.tsx` — staleBanner, tableFooter, latestUpdate, isStale kontrol edildi
- `frontend/src/app/stocks/page.module.css` — .staleBanner, .tableFooter kontrol edildi
- `frontend/src/app/stocks/[symbol]/page.tsx` — analysisDate (state, set, JSX), periodBadge, Bu analiz kontrol edildi
- `frontend/src/app/stocks/[symbol]/page.module.css` — .analysisDate, .periodBadge kontrol edildi
- TypeScript: `npx tsc --noEmit` — hata yok
- Commits 8c54922, 7017f5f mevcut
