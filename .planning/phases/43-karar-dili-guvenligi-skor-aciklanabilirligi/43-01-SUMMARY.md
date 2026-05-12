---
phase: 43-karar-dili-guvenligi-skor-aciklanabilirligi
plan: 01
subsystem: ui
tags: [typescript, nextjs, react, safe-labels, tooltip, recommendation]

# Dependency graph
requires:
  - phase: 42-ai-kalite-sistem-guvenirligi
    provides: recommendation field on StockSummary and ModelPortfolioHolding

provides:
  - safeLabel() helper fonksiyonu — 4 sayfada direktif olmayan etiket gösterimi
  - SAFE_LABEL_MAP sabiti — backend recommendation string -> güvenli Türkçe etiket eşlemesi
  - SAFE_LABEL_TOOLTIP sabiti — her etiket için hover açıklaması
  - stocks/page.tsx: "Görünüm" kolonu ile güvenli etiket + tooltip
  - stocks/[symbol]/page.tsx: AI Karar Kartı signalLabel güvenli etiketle
  - model-portfolio/page.tsx: HoldingRow recommendation güvenli etiket + renk + tooltip
  - page.tsx (dashboard): ideaCard recommendation güvenli etiket + tooltip

affects: [phase-44, phase-45, phase-46, phase-47]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Display-layer label mapping: SAFE_LABEL_MAP Record<string,string> yerel sabiti — DB değişikliği yok"
    - "Tooltip pattern: title={safeLabelTooltip(rec)} her güvenli etiket span/div üzerinde"
    - "Dosya bazlı helper: ortak lib yerine her sayfada kopyalanmış (mevcut proje paterni)"

key-files:
  created: []
  modified:
    - frontend/src/app/stocks/page.tsx
    - frontend/src/app/model-portfolio/page.tsx
    - frontend/src/app/stocks/[symbol]/page.tsx
    - frontend/src/app/page.tsx

key-decisions:
  - "Display-layer mapping: DB recommendation stringleri değiştirilmedi, sadece gösterim katmanında çevrildi"
  - "Dosya bazlı kopyalama: Ortak lib/safeLabel.ts yaratılmadı — mevcut proje paterni her sayfada yerel helper kullanımını tercih eder"
  - "actionPill değiştirilmedi: stocks/[symbol] hero desc ve actionPill zaten kısa karar etiketleri (AL/UZAK DUR/İZLE) kullanıyor, direktif dil sorunu yok"

patterns-established:
  - "safeLabel pattern: tüm recommendation gösterim noktaları safeLabel() üzerinden geçer"
  - "tooltip pattern: title={safeLabelTooltip(rec)} ile hover açıklaması standardize edildi"

requirements-completed: [KARAR-01, KARAR-04]

# Metrics
duration: 2min
completed: 2026-05-12
---

# Phase 43 Plan 01: Karar Dili Güvenliği Summary

**Direktif "GÜÇLÜ AL/SAT" etiketleri 4 sayfada safeLabel() helper ile güvenli, direktif olmayan Türkçe etiketlere (ör. "Yüksek Öncelikli İzleme") çevrildi; her etiketin yanında hover tooltip açıklaması eklendi**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-05-12T18:02:21Z
- **Completed:** 2026-05-12T18:04:13Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- SAFE_LABEL_MAP ve SAFE_LABEL_TOOLTIP sabitleri ile 5 recommendation seviyesi için güvenli etiket + tooltip tanımlandı
- stocks/page.tsx tablosuna "Görünüm" kolonu eklendi; her satırda renk kodlu güvenli etiket ve hover tooltip
- model-portfolio/page.tsx HoldingRow'unda holding.recommendation güvenli etiket + renk + tooltip ile gösteriliyor
- stocks/[symbol]/page.tsx AI Karar Kartı signalLabel bölümü safeLabel(recommendation) + safeLabelTooltip ile güncellendi
- page.tsx dashboard ideaCard'larında stock.recommendation güvenli etiketle gösteriliyor
- Frontend TypeScript build hatası yok (npm run build başarılı)

## Task Commits

1. **Task 1: safeLabel helpers stocks list ve model-portfolio** - `a6076bf` (feat)
2. **Task 2: safeLabel hisse detay ve dashboard ideaCard** - `5e1bd68` (feat)

## Files Created/Modified

- `frontend/src/app/stocks/page.tsx` - SAFE_LABEL_MAP, safeLabel(), safeLabelTooltip(), recSafeColor() eklendi; Görünüm kolonu
- `frontend/src/app/model-portfolio/page.tsx` - SAFE_LABEL_MAP, safeLabel(), safeLabelTooltip(), safeColor() eklendi; HoldingRow güncellendi
- `frontend/src/app/stocks/[symbol]/page.tsx` - SAFE_LABEL_MAP, safeLabel(), safeLabelTooltip() eklendi; signalLabel div güncellendi
- `frontend/src/app/page.tsx` - SAFE_LABEL_MAP, safeLabel(), safeLabelTooltip() eklendi; ideaCard span güncellendi

## Decisions Made

- DB recommendation stringleri değiştirilmedi — sadece display katmanında çevrildi (KARAR-01 gerekliliği)
- Ortak lib dosyası yaratılmadı — mevcut proje paterni dosya bazlı helper kullanımını tercih eder
- stocks/[symbol] hero desc primaryDecision span ve actionPill değiştirilmedi — bunlar zaten kısa 'AL'/'UZAK DUR'/'İZLE' etiketleri, direktif dil sorunu yok

## Deviations from Plan

None - plan exactly as written. Skeleton row kolonu sayısı güncellendi (8→9) — tabloda Görünüm kolonu eklenince iç tutarlılık için.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Güvenli etiket altyapısı tamamlandı; Phase 43 Plan 02 (skor açıklanabilirliği) bağımsız devam edebilir
- KARAR-01 ve KARAR-04 gereksinimleri karşılandı

---
*Phase: 43-karar-dili-guvenligi-skor-aciklanabilirligi*
*Completed: 2026-05-12*
