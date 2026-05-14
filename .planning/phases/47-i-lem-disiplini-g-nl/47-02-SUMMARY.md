---
phase: 47-i-lem-disiplini-g-nl
plan: "02"
subsystem: ui
tags: [typescript, react, portfolio, form, validation]

# Dependency graph
requires:
  - phase: 47-01
    provides: Backend portfolio close endpoint exit_reason ve invalidation_condition alanlarını kabul ediyor

provides:
  - PortfolioPosition interface exit_reason ve invalidation_condition alanlarını içeriyor
  - closePosition API metodu exit_reason zorunlu parametre ile güncellendi
  - addPosition API metodu invalidation_condition opsiyonel parametresi ile güncellendi
  - Pozisyon ekleme modalında "Kararı bozan koşul" textarea
  - Pozisyon kapatma inline formunda çıkış nedeni select + koşullu textarea
  - handleClosePosition validation: exit_reason zorunlu, Diğer seçilince açıklama zorunlu

affects: [portfolio-page, api-client]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Zorunlu select alanı: boş seçenek + validation guard pattern"
    - "Koşullu textarea: state değerine göre göster/gizle"

key-files:
  created: []
  modified:
    - frontend/src/lib/api.ts
    - frontend/src/app/portfolio/page.tsx

key-decisions:
  - "exit_reason frontend'de zorunlu tutuldu; backend Optional kabul etse de kullanıcı her zaman değer seçmeli"
  - "Diğer seçeneği seçilince ek textarea gösteriliyor; final format 'Diğer: [metin]' olarak iletiliyor"
  - "invalidation_condition opsiyonel bırakıldı — trim sonrası boşsa API çağrısına dahil edilmiyor"

patterns-established:
  - "Exit reason validation: boşsa hata → Diğer + boş açıklama ise hata → format hesapla → API çağrısı"

requirements-completed: [GUNLUK-01, GUNLUK-02]

# Metrics
duration: 8min
completed: 2026-05-14
---

# Phase 47 Plan 02: Frontend API Tipleri & Form Mantığı Güncellemesi Summary

**api.ts interface'leri yeni işlem disiplini alanlarıyla genişletildi; pozisyon ekleme formuna "Kararı bozan koşul" ve kapatma formuna zorunlu çıkış nedeni seçici eklendi.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-05-13T23:04:00Z
- **Completed:** 2026-05-13T23:12:20Z
- **Tasks:** 2/2
- **Files modified:** 2

## Accomplishments

### Task 1: api.ts interface ve metot tiplerini genişlet

`PortfolioPosition` interface'e `exit_reason: string | null` ve `invalidation_condition: string | null` eklendi. `addPosition` data tipine `invalidation_condition?: string` eklendi. `closePosition` data tipine `exit_reason: string` (zorunlu) eklendi.

### Task 2: Form state, handler ve JSX güncelle

- `PositionForm` tipine ve `EMPTY_FORM`'a `invalidation_condition: string` eklendi
- `closeForm` state tipi `exit_reason` ve `exit_reason_other` içerecek şekilde genişletildi
- `handleClosePosition` fonksiyonuna GUNLUK-02 validation guard'ları ve `exit_reason` format hesaplama eklendi
- `handleAddPosition` çağrısına `invalidation_condition` dahil edildi
- Modal forma "Kararı bozan koşul" textarea eklendi (GUNLUK-01)
- Inline close form'a çıkış nedeni `<select>` (4 seçenek) + `Diğer` için koşullu `<textarea>` eklendi (GUNLUK-02)

## Commits

| Hash | Message | Files |
|------|---------|-------|
| d62ba65 | feat(47-02): api.ts — PortfolioPosition, addPosition, closePosition genislet | api.ts |
| 21ae290 | feat(47-02): portfolio page — form state, handler ve JSX guncelle | portfolio/page.tsx |

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- frontend/src/lib/api.ts: exit_reason, invalidation_condition present
- frontend/src/app/portfolio/page.tsx: invalidation_condition, exit_reason, Kararı bozan present
- Commits d62ba65, 21ae290 verified in git log
