---
gsd_state_version: 1.0
milestone: v5.0
milestone_name: LLM Entegrasyonlu Yatırım Asistanı
status: unknown
stopped_at: Completed 37-01-PLAN.md (Günlük Gemini Piyasa Özeti)
last_updated: "2026-05-08T11:03:22.181Z"
progress:
  total_phases: 14
  completed_phases: 7
  total_plans: 12
  completed_plans: 17
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-05-08)

**Core value:** Kullanıcının "bu hisseyi neden almalıyım?" sorusuna hem veriyle hem açıklamayla cevap vermek — karar kullanıcıda, anlayış asistanda.
**Current milestone:** v5.0 — LLM Entegrasyonlu Yatırım Asistanı
**Previous milestone:** v4.0 — Kişisel Yatırım Asistanı (Phases 28-29 tamamlandı; 30-33 v5.0'a taşındı)

## Current Position

Phase: 36
Plan: 36-01 complete

## v5.0 Phases

- [x] Phase 34: Frontend Tasarım Düzeltmeleri — 6 prototype audit tasarım tutarsızlığı giderilir ✅ (2026-05-08)
- [ ] Phase 35: Gemini LLM Altyapısı — Backend Gemini 2.0 Flash servis katmanı, quota fallback
- [ ] Phase 36: Keşif & Hisse Detay + AI Analizi — Skorlu liste, detay sayfası, on-demand Gemini analizi
- [ ] Phase 37: Haberler + Günlük Piyasa Özeti — KAP + basın birleşik akış, otomatik günlük özet
- [ ] Phase 38: Portföy — Alım-satım, P&L, BIST100 karşılaştırma, watchlist
- [ ] Phase 39: Model Portföy + AI Kararları — Özerk haftalık portföy, Gemini Türkçe gerekçe, geçmiş, karşılaştırma

## Phase Dependency Map

```
Phase 29 (tamamlandı)
    └── Phase 34: Tasarım Düzeltmeleri
            └── Phase 35: Gemini LLM Altyapısı
                    ├── Phase 36: Keşif & Hisse Detay + AI Analizi
                    └── Phase 37: Haberler + Günlük Piyasa Özeti

Phase 29 (tamamlandı)
    └── Phase 38: Portföy
            └── Phase 39: Model Portföy + AI Kararları
                    └── (also depends on Phase 35)
```

## Performance Metrics

| Metric | v3.1 | v4.0 | v5.0 |
|--------|-------|-------|-------|
| Phases | 6 | 6 (planned) | 6 |
| Plans | 7 | 14 (planned) | 13 (planned) |
| Requirements | 25/25 | 23/23 mapped | 27/27 mapped |
| Started | 2026-04-28 | 2026-05-04 | 2026-05-08 |
| Completed | 2026-04-29 | — (absorbed) | — |
| Phase 34 P01 | 117 | 2 tasks | 2 files |
| Phase 34 P02 | 3 | 3 tasks | 6 files |
| Phase 35 P01 | 224 | 2 tasks | 4 files |
| Phase 36 P01 | 25 min | 3 tasks | 5 files modified + 1 created |
| Phase 37-haberler-g-nl-k-ai-ozeti P01 | 15 | 3 tasks | 8 files |

### v4.0 Completed Plans (reference)

| Phase | Plan | Score | Tasks | Files |
|-------|------|-------|-------|-------|
| Phase 28 P01 | 28-01-PLAN.md | 5 | 3 | 6 |
| Phase 28 P02 | 28-02-PLAN.md | 3 | 3 | 2 |
| Phase 28 P03 | 28-03-PLAN.md | 220 | 3 | 3 |
| Phase 29 P01 | 29-01-PLAN.md | 2 | 3 | 3 |
| Phase 29 P02 | 29-02-PLAN.md | 5 | 3 | 2 |

## Accumulated Context

### Key Decisions

- On-demand AI analizi (Gemini) — sadece "Analiz Et" butonunda tetiklenir; API maliyeti kontrolü
- BIST100 evreni — likit, veri kaliteli, odaklı başlangıç (BIST250+ v2'ye bırakıldı)
- Giriş yok — kişisel araç, tek kullanıcı, sürtünmeyi azaltır
- Model portföy özerk — AI kendi kararlarını verir, kullanıcı karşılaştırır
- Kripto yok — odak dışı, v1 için gereksiz
- Gemini 2.0 Flash free tier — DeepSeek'in yerini alıyor; 15 req/min, 1500 req/gün yeterli
- LLM güvenli fallback — Gemini quota dolsa endpoint hata değil placeholder döner; uygulama çökmez
- v4.0 Phases 30-33 absorbe edildi — v5.0'da Gemini entegrasyonuyla birlikte teslim edilecek
- [28-01] Session-scoped app_client in conftest.py avoids APScheduler + asyncpg event loop collision across test modules using TestClient
- [28-01] xfail(strict=False) for endpoint stubs in Plans 28-02/03 — tests collect cleanly, XPASS non-fatal when local DB has data
- [28-01] FOREX_PAIRS uses Yahoo Finance ticker as key (USDTRY=X), human label as value (USD/TRY) — consistent with downstream endpoint response shape
- [28-02] Compute change_pct from last 2 CommodityPrice rows — not from change_pct column (often NULL, Pitfall 6)
- [28-02] Volume=0 masked to None for BIST100 index — index volume is unreliable (Pitfall 1)
- [28-02] _latest_close_and_date is local helper in market.py — avoids cross-router coupling with macro.py
- [28-03] No cache on /market/opportunities — score freshness critical, endpoint reflects latest ScoringEngine run immediately
- [28-03] overall_score IS NOT NULL guard ensures unscored stocks excluded from opportunities list (Pitfall 3 honored)
- [28-03] Mock-based deterministic DISC-01 test: pre-sort list in test data since SQL ORDER BY cannot be enforced in MagicMock

### Known Constraints

- AI çağrıları yalnızca kullanıcı "Analiz Et" dediğinde veya günde bir otomatik özet için; gereksiz çağrı yok
- Stack: Next.js (frontend, Vercel) + FastAPI (backend, Railway) + PostgreSQL
- Tamamen Türkçe arayüz
- Web-first, responsive — native app yok
- Gemini 2.0 Flash free tier: 15 req/min, 1500 req/gün

### Blockers

None.

## Session Continuity

**Last session:** 2026-05-08T11:03:22.179Z
**Stopped at:** Completed 37-01-PLAN.md (Günlük Gemini Piyasa Özeti)
**Next action:** Continue Phase 36 or plan remaining phases (37-39)

---
