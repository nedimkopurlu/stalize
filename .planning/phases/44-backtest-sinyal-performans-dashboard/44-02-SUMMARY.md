---
phase: 44-backtest-sinyal-performans-dashboard
plan: "02"
subsystem: frontend
tags: [backtest, signals, performance, table, filters, kpi]
dependency_graph:
  requires:
    - 44-01 (backend API endpoints: /signals/outcomes, /signals/calibration)
  provides:
    - /backtest page route with full signal performance dashboard
  affects:
    - frontend/src/app/backtest/
tech_stack:
  added: []
  patterns:
    - useEffect + loadData() pattern (consistent with stocks/page.tsx)
    - Promise.all for parallel API calls
    - Client-side filtering on loaded data
    - SAFE_LABEL_MAP display-layer mapping (KARAR-01)
key_files:
  created:
    - frontend/src/app/backtest/page.tsx
    - frontend/src/app/backtest/backtest.module.css
  modified: []
decisions:
  - Promise.all fetches 1w + 1m calibration simultaneously — no sequential loading penalty
  - Client-side action/outcome filtering — avoids extra API calls for each filter change
  - Period filter triggers loadData (server-side limit) — reduces payload size for shorter periods
  - Separate calibration1m state alongside calibration (1w) — enables 4th KPI card
metrics:
  duration_seconds: 113
  tasks_completed: 2
  files_created: 2
  files_modified: 0
  completed_date: "2026-05-13"
---

# Phase 44 Plan 02: Backtest Sayfası Summary

**One-liner:** /backtest rotasında sinyal performans tablosu — 4 KPI kart, 3 istemci filtresi, 7 sütunlu backtest tablosu ve boş durum ekranı.

## Objective

Kullanıcının geçmiş sinyal kararlarının hit ratio ve getiri istatistiklerini somut bir tabloda görmesi. 44-01'de oluşturulan backend API endpointlerini frontend'e bağlamak.

## What Was Built

### Task 1: page.tsx (344 satır)

- `'use client'` direktifi, `useState`/`useEffect`, `AppShell` wrapper
- `Promise.all` ile paralel API çağrısı: `getSignalOutcomes(limit, '1w')` + `getSignalCalibration('1w', 1)` + `getSignalCalibration('1m', 1)`
- **4 KPI kart (BACKTEST-03):**
  - Toplam Sinyal: `outcomes.length`
  - 1H Başarı Oranı: `calibration?.overall.success_rate` — yeşil/kırmızı renk
  - Ort. 1H Getiri: `calibration?.overall.avg_return_pct`
  - Ort. 1M Getiri: `calibration1m?.overall.avg_return_pct`
- **3 filtre (BACKTEST-02):**
  - Dönem (1A/3A/6A): button grubu, `setPeriod` → `useEffect` ile `loadData` tetikler
  - Güvenli Etiket: `<select>` → `action` değerine göre istemci tarafı filtre
  - Başarı Durumu: `<select>` → `outcome_1w` değerine göre istemci tarafı filtre
- **7 sütunlu tablo (BACKTEST-01):** Tarih | Hisse | Güvenli Etiket | 1H % | 1M % | BIST100 Relatif | Başarılı mı
- **Boş durum (BACKTEST-04):** "Henüz backtest verisi yok — sistem sinyal topluyor" bar chart SVG ikonu ile
- `SAFE_LABEL_MAP` + `ACTION_TO_REC` güvenli etiket dönüşümü (KARAR-01 uyumlu)
- Özet rozet grubu: Başarılı / Başarısız / Bekliyor sayıları filtre barında

### Task 2: backtest.module.css (262 satır)

- Tüm gerekli CSS sınıfları: `.container`, `.kpiGrid`, `.kpiCard`, `.filterBar`, `.filterBtn`, `.filterBtnActive`, `.filterSelect`, `.tableWrapper`, `.table`, `.symbolCell`, `.emptyState`, `.emptyIcon`
- Rozet stilleri: `.summaryBadges`, `.badgeSuccess`, `.badgeFailure`, `.badgePending`
- CSS değişkenleri: `var(--bg-card)`, `var(--border)`, `var(--text)`, `var(--text-muted)`, `var(--accent)`, `var(--accent-green)`, `var(--accent-red)`
- Responsive: `@media (max-width: 768px)` — 2 sütunlu KPI grid, kompakt tablo padding

## Commits

| Task | Commit | Message |
|------|--------|---------|
| Task 1 | c8eb47e | feat(44-02): backtest sayfası page.tsx — KPI kartlar, 3 filtre, 7 sütunlu tablo |
| Task 2 | a698152 | feat(44-02): backtest.module.css — sayfa stilleri ve tüm CSS sınıfları |

## Requirements Satisfied

| Req | Description | Status |
|-----|-------------|--------|
| BACKTEST-01 | 7 sütunlu sinyal performans tablosu | ✅ Complete |
| BACKTEST-02 | Dönem, güvenli etiket ve başarı durumu filtreleri | ✅ Complete |
| BACKTEST-03 | KPI kartlar (toplam sinyal, başarı oranı, ortalama getiri) | ✅ Complete |
| BACKTEST-04 | Boş durum mesajı — sistem sinyal topluyor | ✅ Complete |

## Deviations from Plan

### Auto-added Improvements

**1. [Rule 2 - Enhancement] Özet rozet grubu eklendi**
- **Found during:** Task 1 — filtre barı tasarımı
- **Enhancement:** `summary.success`, `summary.failure`, `summary.pending` sayılarını filtre barına rozet olarak eklendi
- **Reason:** API zaten bu veriyi `SignalOutcomesResponse.summary` içinde döndürüyor; kullanıcıya filtreden önce genel görünüm verir
- **Files modified:** page.tsx (summaryBadges), backtest.module.css (.badgeSuccess/.badgeFailure/.badgePending)

None — plan tam olarak uygulandı; tek ek rozet grubu plan kapsamını genişletmeden kullanıcı deneyimini iyileştirdi.

## Known Stubs

None — tüm veri bağlantıları gerçek API çağrılarına bağlı. Boş durum sadece API'den `items: []` geldiğinde gösterilir.

## Self-Check

- [x] `frontend/src/app/backtest/page.tsx` — 344 satır, oluşturuldu
- [x] `frontend/src/app/backtest/backtest.module.css` — 262 satır, oluşturuldu
- [x] TypeScript: `npx tsc --noEmit` — 0 hata
- [x] `grep -c "getSignalOutcomes"` → 3 eşleşme (1 import, 1 çağrı, 1 tip)
- [x] `grep -c "Henüz backtest verisi yok"` → 1 eşleşme
- [x] 7 sütun başlığı mevcut
- [x] Commit c8eb47e ve a698152 oluşturuldu

## Self-Check: PASSED
