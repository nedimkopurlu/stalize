# Phase 44: Backtest & Sinyal Performans Dashboard - Context

**Gathered:** 2026-05-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Mevcut sinyal snapshot + outcome evaluation altyapısı (backend/app/services/signal_tracking.py, /signals/outcomes ve /signals/calibration endpoint'leri) kullanıcıya görünür hale getirilir. Yeni `/backtest` sayfası oluşturulur; sinyal performans tablosu, hit ratio KPI kartları ve filtreler eklenir.

</domain>

<decisions>
## Implementation Decisions

### Dashboard Konumu & Filtreler
- Yeni `/backtest` route'u — `/app/backtest/page.tsx` (ayrı sayfa, temiz navigation)
- Filtreler: dönem (son 1A/3A/6A), karar etiketi (güvenli etiketler), başarı durumu — BACKTEST-02
- Hit ratio özeti: tablonun üstünde 3 KPI kartı — toplam sinyal sayısı, başarı oranı %, ortalama 1h ve 1m getiri
- Boş durum: "Henüz backtest verisi yok — sistem sinyal topluyor" + ikon — BACKTEST-04

### Tablo Tasarımı & Backend Entegrasyonu
- 7 sütun: Sinyal Tarihi, Hisse, Güvenli Etiket, 1H Getiri %, 1M Getiri %, BIST100 Relatif, Başarılı mı — BACKTEST-01
- Mevcut endpoint'ler kullanılır: GET /signals/outcomes (tablo) + GET /signals/calibration (hit ratio)
- Relatif performans: `relative_1w`/`relative_1m` backend alanları varsa göster, yoksa "—"
- Sidebar'a yeni "Backtest" nav item eklenir (Haberler'den sonra)

### Claude's Discretion
- CSS sınıf isimleri ve module yapısı
- KPI kart renk kodlaması (yeşil/kırmızı/mavi)
- Başarı/başarısız renk kodlaması tablo satırında

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/api/signals.py`: GET /signals/outcomes (limit, action, outcome, horizon filtreli) — tam hazır
- `backend/app/api/signals.py`: GET /signals/calibration (horizon, min_count) — hit ratio için hazır
- `backend/app/models/signal.py`: SignalDecision modeli — tarih, hisse, action, outcome_1w, outcome_1m, relative_1w, relative_1m
- `frontend/src/components/Sidebar.tsx`: NAV_ITEMS array — yeni item eklenecek
- `frontend/src/lib/api.ts`: api client — yeni endpoint metodları eklenecek
- Phase 43'ten `SAFE_LABEL_MAP` — backtest sayfasında da kullanılacak (import veya tekrar tanım)

### Established Patterns
- Sayfa yapısı: `'use client'`, `useState` + `useEffect` + `loadData()` pattern
- CSS Modules: `page.module.css` co-located
- Tablo: stocks/page.tsx tablo yapısı referans
- KPI kartlar: dashboard page.tsx'teki kpiCard pattern

### Integration Points
- `frontend/src/components/Sidebar.tsx` — NAV_ITEMS'e { href: '/backtest', label: 'Backtest', Icon: IconChartBar } ekle
- `frontend/src/lib/api.ts` — `getSignalOutcomes(params)` ve `getSignalCalibration(params)` metodları ekle
- `frontend/src/app/backtest/page.tsx` — yeni sayfa oluştur
- `frontend/src/app/backtest/backtest.module.css` — yeni CSS

</code_context>

<specifics>
## Specific Ideas

- Dönem filtresi: "1A" → limit=30 sinyal, "3A" → limit=90, "6A" → limit=180 (date-based filtering ideal ama limit proxy olarak kullanılabilir)
- Başarı ikonu: ✓ yeşil / ✗ kırmızı / — gri (outcome null)
- KPI kartlar: "Toplam Sinyal: N", "Başarı Oranı: %X (1H) | %Y (1M)", "Ort. Getiri: +X% (1H) | +Y% (1M)"

</specifics>

<deferred>
## Deferred Ideas

- Date-range picker (filtrede date-based sorgulama) — şimdilik limit proxy yeterli
- Sektör bazlı backtest filtresi — v2'ye bırakıldı

</deferred>
