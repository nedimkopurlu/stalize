---
gsd_state_version: 1.0
milestone: v6.0
milestone_name: Karar Güvenliği & Sistem Olgunlaşması
status: unknown
last_updated: "2026-05-13T22:50:03.184Z"
progress:
  total_phases: 22
  completed_phases: 13
  total_plans: 22
  completed_plans: 27
---

# Project State

## Project Reference

See: `.planning/PROJECT.md`

**Core value:** Kullanıcının "bu hisseyi neden almalıyım?" sorusuna hem veriyle hem açıklamayla cevap vermek — karar kullanıcıda, anlayış asistanda.
**Current milestone:** v6.0 — Karar Güvenliği & Sistem Olgunlaşması 🔄 IN PROGRESS
**Previous milestone:** v5.1 — Kapsamlı Bug Fix & Kalite İyileştirme ✅ COMPLETE (Phases 40-42)
**Previous milestone:** v5.0 — LLM Entegrasyonlu Yatırım Asistanı ✅ COMPLETE

## Current Position

Phase: 46 (portföy-risk-yönetimi) — EXECUTING
Plan: 2 of 2

## v5.0 Phases

- [x] Phase 34: Frontend Tasarım Düzeltmeleri ✅ (2026-05-08)
- [x] Phase 35: Gemini LLM Altyapısı ✅ (2026-05-08)
- [x] Phase 36: Hisse Detay + AI Analizi ✅ (2026-05-08)
- [x] Phase 37: Haberler + Günlük Piyasa Özeti ✅ (2026-05-08)
- [x] Phase 38: Portföy — PORT-02 pozisyon kapatma + gerçek K/Z ✅ (2026-05-08)
- [x] Phase 39: Model Portföy + AI Kararları ✅ (2026-05-08)

## v5.1 Phases (Tamamlandı)

- [x] Phase 40: UI/UX Kapsamlı Görsel İyileştirme ✅ (2026-05-08)
- [x] Phase 41: Veri Doğruluğu & Eksik Fonksiyonlar ✅ (2026-05-08)
- [x] Phase 42: AI Kalite & Sistem Güvenilirliği ✅ (2026-05-08)

## v6.0 Phases

- [x] Phase 43: Karar Dili Güvenliği & Skor Açıklanabilirliği ✅ (2026-05-12)
  - Requirements: KARAR-01, KARAR-02, KARAR-03, KARAR-04, SKOR-01, SKOR-02, SKOR-03
  - Goal: "GÜÇLÜ AL/SAT" direktif etiketler güvenli dile çevrilir; hisse detay sayfasında skor bileşen dökümü ve veri bütünlüğü göstergesi eklenir
- [x] Phase 44: Backtest & Sinyal Performans Dashboard ✅ (2026-05-13)
  - Requirements: BACKTEST-01, BACKTEST-02, BACKTEST-03, BACKTEST-04
  - Goal: Mevcut sinyal altyapısı kullanıcıya görünür; hit ratio ve getiri tablosu sunulur
- [x] Phase 45: Veri Tazeliği & Sistem Sağlığı ✅ (2026-05-14)
  - Requirements: VERI-01, VERI-02, VERI-03, VERI-04
  - Goal: Son güncelleme zamanı UI'da; stale data uyarısı; AI analizine veri tarihi notu
- [x] Phase 46: Portföy Risk Yönetimi ✅ (2026-05-14)
  - Requirements: RISK-01 ✅, RISK-02 ✅, RISK-03 ✅, RISK-04 ✅
  - Goal: Sektör dağılımı görsel; yoğunlaşma uyarıları; risk özeti kartı
- [ ] Phase 47: İşlem Disiplini & Günlüğü ⬜ Not started
  - Requirements: GUNLUK-01, GUNLUK-02, GUNLUK-03, GUNLUK-04
  - Goal: Kararı bozan koşul alanı; çıkış nedeni kaydı; kapalı pozisyon istatistiği

## Phase Dependency Map

```
Phase 42 (v5.1 tamamlandı)
    └── Phase 43: Karar Dili & Skor Açıklanabilirliği
            ├── Phase 44: Backtest Dashboard
            ├── Phase 45: Veri Tazeliği (parallel with 44)
            └── Phase 46: Portföy Risk Yönetimi
                    └── Phase 47: İşlem Disiplini & Günlüğü
```

## v5.x Phase Dependency Map (Arşiv)

```
Phase 39 (v5.0 tamamlandı)
    └── Phase 40: UI/UX Kapsamlı Görsel İyileştirme
            └── Phase 41: Veri Doğruluğu & Eksik Fonksiyonlar
                    └── Phase 42: AI Kalite & Sistem Güvenilirliği
```

## Delivered This Milestone

| Phase | Plan | Key Deliverables |
|-------|------|-----------------|
| Phase 40 | UI/UX | Mobile responsive, empty states, hardcoded colors |
| Phase 41 | DATA/FEAT | NaN guards, null safety, fundGrid skeleton, BistComparisonChart |
| Phase 42 | AI | Groq birincil sağlayıcı, derinleştirilmiş promptlar, model portföy gerekçe kalitesi |
| Phase 43 | KARAR/SKOR | safeLabel 4 sayfada, skor dökümü progress bar, bileşen sayacı, volatilite uyarısı |
| Phase 45 | VERI | stale-data banner, güncelleme saati altbilgisi, fundamental period badge, AI analiz tarihi |

## Requirements Satisfied (v5.0)

| Req | Status |
|-----|--------|
| DESIGN-01..06 | ✅ |
| LLM-01..04 | ✅ |
| DISC-03 | ✅ (navigasyon mevcut) |
| STCK-01 | ✅ (grafik mevcut) |
| STCK-02 | ✅ (temel metrikler + tooltip) |
| STCK-03 | ✅ (teknik göstergeler mevcut) |
| STCK-04 | ✅ (Analiz Et + session cache) |
| STCK-05 | ✅ (intelligence sayfasında) |
| STCK-06 | ✅ (intelligence sayfasında) |
| NEWS-01 | ✅ (intelligence sayfası mevcut) |
| PORT-01..05 | ✅ |
| MODEL-01..04 | ✅ |

## v5.1 Requirements to Satisfy

| Req | Phase | Status |
|-----|-------|--------|
| UI-01 | Phase 40 | ✅ Complete |
| UI-02 | Phase 40 | ✅ Complete |
| UI-03 | Phase 40 | ✅ Complete |
| UI-04 | Phase 40 | ✅ Complete |
| UI-05 | Phase 40 | ✅ Complete |
| DATA-01 | Phase 41 | ✅ Complete |
| DATA-02 | Phase 41 | ✅ Complete |
| DATA-03 | Phase 41 | ✅ Complete |
| FEAT-01 | Phase 41 | ✅ Complete |
| FEAT-02 | Phase 41 | ✅ Complete |
| FEAT-03 | Phase 41 | ✅ Complete |
| AI-01 | Phase 42 | ✅ Complete |
| AI-02 | Phase 42 | ✅ Complete |
| AI-03 | Phase 42 | ✅ Complete |
| AI-04 | Phase 42 | ✅ Complete |

## v6.0 Requirements to Satisfy

| Req | Phase | Status |
|-----|-------|--------|
| KARAR-01 | Phase 43 | ✅ Complete |
| KARAR-02 | Phase 43 | ✅ Complete |
| KARAR-03 | Phase 43 | ✅ Complete |
| KARAR-04 | Phase 43 | ✅ Complete |
| SKOR-01 | Phase 43 | ✅ Complete |
| SKOR-02 | Phase 43 | ✅ Complete |
| SKOR-03 | Phase 43 | ✅ Complete |
| BACKTEST-01 | Phase 44 | ⬜ Pending |
| BACKTEST-02 | Phase 44 | ⬜ Pending |
| BACKTEST-03 | Phase 44 | ⬜ Pending |
| BACKTEST-04 | Phase 44 | ⬜ Pending |
| VERI-01 | Phase 45 | ✅ Complete |
| VERI-02 | Phase 45 | ✅ Complete |
| VERI-03 | Phase 45 | ✅ Complete |
| VERI-04 | Phase 45 | ✅ Complete |
| RISK-01 | Phase 46 | ✅ Complete |
| RISK-02 | Phase 46 | ✅ Complete |
| RISK-03 | Phase 46 | ✅ Complete |
| RISK-04 | Phase 46 | ✅ Complete |
| GUNLUK-01 | Phase 47 | ⬜ Pending |
| GUNLUK-02 | Phase 47 | ⬜ Pending |
| GUNLUK-03 | Phase 47 | ⬜ Pending |
| GUNLUK-04 | Phase 47 | ⬜ Pending |

## Accumulated Context

### Key Decisions

- riskGuard fetched in separate useEffect after positions load — totalValue derived from active positions (v6.0 46-01)
- sectorDist CSS yatay bar chart — harici kütüphane yok, exposure_pct% genişlik (v6.0 46-01, RISK-01)
- On-demand AI analizi (Gemini) — sadece "Analiz Et" butonunda tetiklenir; API maliyeti kontrolü
- BIST100 evreni — likit, veri kaliteli, odaklı başlangıç (BIST250+ v2'ye bırakıldı)
- Giriş yok — kişisel araç, tek kullanıcı, sürtünmeyi azaltır
- Model portföy özerk — AI kendi kararlarını verir, kullanıcı karşılaştırır
- Gemini 2.0 Flash free tier — 15 req/min, 1500 req/gün yeterli
- LLM güvenli fallback — Gemini quota dolsa endpoint hata değil placeholder döner
- In-memory cache günlük özet için — server restart temizler, basit ve yeterli
- Closed positions: yfinance fetch skip, activePositions-only for live calculations
- v5.1 watchlist sync: localStorage üzerinden — DB'ye taşıma v2'ye bırakıldı
- Display-layer label mapping (v6.0 43-01): DB recommendation stringleri değiştirilmedi, display katmanında güvenli etikete çevrildi (KARAR-01)
- Dosya bazlı helper kopyalama (v6.0 43-01): ortak lib yerine her sayfada yerel safeLabel — mevcut proje paterni
- Volatilite proxy listede daily_change_pct >%4 (v6.0 43-02): 20g fiyat geçmişi hisse listesinde mevcut değil, günlük hareket proxy olarak kullanıldı
- Skor Dökümü bölümü hero'dan sonra ayrı section (v6.0 43-02): scoreCard içinde değil, tam genişlikte editorial düzende
- Promise.all 1w+1m calibration eş zamanlı (v6.0 44-02): sıralı yükleme yerine paralel fetch, KPI kartlarda gecikme yok
- Client-side action/outcome filtreleme (v6.0 44-02): her filtre için ekstra API çağrısı yerine yüklenmiş veriye client filtre
- Dönem filtresi server-side limit, diğer filtreler client-side (v6.0 44-02): kısa dönemlerde payload azalır; etiket/başarı filtreleri anlık tepki verir
- updated_at opsiyonel (v6.0 45-01): StockSummary.updated_at?: string | null — mevcut componentler degisiklik gerektirmez, geri donuk uyumlu
- DateTime isoformat ile None guard (v6.0 45-01): s.updated_at.isoformat() if s.updated_at else None — null safety
- latestUpdate Math.max client-side (v6.0 45-02): tüm hisselerin updated_at'ından en son tarih — sunucuda aggregate endpoint yok
- 8 saat stale eşiği (v6.0 45-02): Türkiye piyasası 09:00-18:00 EEST; geceleri/hafta sonu kapanma için uygun eşik
- analysisDate state string (v6.0 45-02): generated_at format dönüşümü render yerine set anında yapılır; fallback Date.now()
- periodBadge vendor-data-missing gizlenir (v6.0 45-02): null ile aynı davranış — boş period badge gösterilmez
- concentrationAlerts sorted by pct desc — highest risk alert shown first (v6.0 46-02)
- riskAlerts section guarded by length > 0 — no empty space when threshold not breached (v6.0 46-02, RISK-02, RISK-03)

### Known Technical Debt

- `google.generativeai` deprecated → `google.genai` migration pending (v2)
- Per-holding Gemini rationale deferred — rate limit riski (v2)
- Model portfolio strategy templates clickable — v2
- `google.generativeai` FutureWarning in tests — non-blocking

### Blockers

None.

## Session Continuity

**Last session:** 2026-05-14T00:09:14Z
**Completed:** Phase 46 Plan 02 — yoğunlaşma uyarıları (RISK-02, RISK-03) — Phase 46 DONE
**Next action:** Execute Phase 47 — İşlem Disiplini & Günlüğü (GUNLUK-01..04)

---
