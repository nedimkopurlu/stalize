---
gsd_state_version: 1.0
milestone: v7.0
milestone_name: Analiz Kalitesi & Sistem Bütünlüğü
status: completed
last_updated: "2026-05-16T11:23:51.874Z"
last_activity: 2026-05-16
progress:
  total_phases: 25
  completed_phases: 17
  total_plans: 31
  completed_plans: 36
---

# Project State

## Project Reference

See: `.planning/PROJECT.md`

**Core value:** Kullanıcının "bu hisseyi neden almalıyım?" sorusuna hem veriyle hem açıklamayla cevap vermek — karar kullanıcıda, anlayış asistanda.
**Current milestone:** v7.0 — Analiz Kalitesi & Sistem Bütünlüğü ✅ COMPLETE
**Previous milestone:** v6.0 — Karar Güvenliği & Sistem Olgunlaşması ✅ COMPLETE (Phases 43-47)

## Current Position

Phase: —
Plan: —
Status: v7.0 COMPLETE ✅ — all 8 phases delivered, 21/21 requirements met
Last activity: 2026-05-16

## v7.0 Phases

- [x] Phase 48: Veri Kalitesi Temeli ✅ (2026-05-15)
  - Requirements: VKL-01, VKL-02, TECH-01
  - Goal: yfinance USD→TRY sanity check layer, data_quality_score per stock, safeLabel() tek kaynak
  - Depends on: Phase 47 (v6.0 complete)

- [x] Phase 49: Veri Zenginleştirme ✅ (2026-05-15)
  - Requirements: VKL-03, VKL-04, KAP-01, KAP-02
  - Goal: Tavan/taban badge, likidite skoru (Amihud), KAP duyuru kategorilendirme
  - Depends on: Phase 48

- [x] Phase 50: Market Regime Engine ✅ (2026-05-15)
  - Requirements: REJ-01, REJ-02
  - Goal: ADX+EMA200+ATR kural tabanlı rejim tespiti, USD-adjusted XU100.IS, regime badge
  - Depends on: Phase 48

- [x] Phase 51: Sektör Bazlı Skorlama ✅ (2026-05-15)
  - Requirements: SEK-01, SEK-02, SEK-03
  - Goal: Banka P/TBV+ROE, GYO P/B proxy, Holding NAV yaklaşımı
  - Depends on: Phase 48

- [x] Phase 52: Portföy Analizi ✅ (2026-05-15)
  - Requirements: PORT-01, PORT-02, PORT-03
  - Goal: Portföy beta, korelasyon matrisi, pozisyon büyüklüğü rehberi
  - Depends on: Phase 48

- [x] Phase 53: Türkçe NLP & Sentiment ✅ (2026-05-15)
  - Requirements: NLP-01, NLP-02
  - Goal: VADER kaldır, GPT-4o-mini KAP sentiment, Türkçe RSS kural seti
  - Depends on: Phase 49

- [x] Phase 54: Backtest Kalitesi ✅ (2026-05-15)
  - Requirements: BACK-01, BACK-02, REJ-03
  - Goal: Likidite bazlı slipaj, %0.1 komisyon, rejim bazlı backtest filtreleme
  - Depends on: Phase 50, Phase 52

- [x] Phase 55: UI — Hisse Detay & Ön-işlem Checklist ✅ (2026-05-15)
  - Requirements: UI-01, UI-02
  - Goal: Detay sayfa hiyerarşisi, 7 maddelik ön-işlem checklist (otomatik doldurulmuş)
  - Depends on: Phase 49, Phase 50, Phase 52, Phase 54

## Phase Dependency Map

```
Phase 47 (v6.0 tamamlandı)
    └── Phase 48: Veri Kalitesi Temeli
            ├── Phase 49: Veri Zenginleştirme
            │       └── Phase 53: Türkçe NLP & Sentiment
            ├── Phase 50: Market Regime Engine
            │       └── Phase 54: Backtest Kalitesi
            ├── Phase 51: Sektör Bazlı Skorlama
            └── Phase 52: Portföy Analizi
                    └── Phase 54: Backtest Kalitesi
                            └── Phase 55: UI — Hisse Detay & Ön-işlem Checklist
                    (Phase 49, 50 da Phase 55'e bağımlı)
```

## v6.0 Phases (Tamamlandı)

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
  - Requirements: RISK-01, RISK-02, RISK-03, RISK-04
  - Goal: Sektör dağılımı görsel; yoğunlaşma uyarıları; risk özeti kartı
- [x] Phase 47: İşlem Disiplini & Günlüğü ✅ (2026-05-14)
  - Requirements: GUNLUK-01, GUNLUK-02, GUNLUK-03, GUNLUK-04
  - Goal: Kararı bozan koşul alanı; çıkış nedeni kaydı; kapalı pozisyon istatistiği

## Accumulated Context

### Key Decisions

- data_quality_score scoring formula: 100 base, -30 per USD-suspicious ratio (pe<2, pb<0.05), -10 per null field (pe, pb, ev_ebitda, net_income, revenue), clamped [0,100]; uses net_income not net_profit (48-01, VKL-01/02)
- _list_data_quality_score helper replaced by DB column s.data_quality_score in /stocks list endpoint (48-01, VKL-02)
- exit_reason String(50), invalidation_condition Text — nullable, inspector-pattern idempotent migration 007 (v6.0 47-01, GUNLUK-01/02)
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
- Dosya bazlı helper kopyalama (v6.0 43-01): ortak lib yerine her sayfada yerel safeLabel — mevcut proje paterni; v7.0 Phase 48'de TECH-01 ile StockHelpers.tsx'e taşınacak
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
- v7.0 NLP: BERTurk/HuggingFace kaldırıldı (Railway 512MB RAM sınırı); OpenAI GPT-4o-mini batch sentiment kullanılıyor (NLP-01)
- v7.0 Sector scoring: yfinance sektör string normalizasyon haritası gerekiyor; Phase 51 öncesinde live verification yapılmalı

### Known Technical Debt

- `google.generativeai` deprecated → `google.genai` migration pending (v2)
- Per-holding Gemini rationale deferred — rate limit riski (v2)
- Model portfolio strategy templates clickable — v2
- `google.generativeai` FutureWarning in tests — non-blocking

### Blockers

None.

## Session Continuity

**Last session:** 2026-05-15T18:53:42.064Z
**Completed:** Phase 48 complete — VKL-01, VKL-02, TECH-01 delivered; 7/7 verification checks passed
**Next action:** Plan + execute Phase 49 (Veri Zenginleştirme — VKL-03, VKL-04, KAP-01, KAP-02)

---
