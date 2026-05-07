---
gsd_state_version: 1.0
milestone: v4.0
milestone_name: Kişisel Yatırım Asistanı
status: unknown
last_updated: "2026-05-07T17:22:01.547Z"
progress:
  total_phases: 12
  completed_phases: 3
  total_plans: 7
  completed_plans: 12
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-05-04)

**Core value:** Kullanıcının "bu hisseyi neden almalıyım?" sorusuna hem veriyle hem açıklamayla cevap vermek — karar kullanıcıda, anlayış asistanda.
**Current milestone:** v4.0 — Kişisel Yatırım Asistanı
**Previous milestone:** v3.1 — Audit Düzeltmeleri (tamamlandı 2026-04-29)

## Current Position

Phase: 30
Plan: Not started

## v4.0 Phases

- [ ] Phase 28: Veri Altyapısı — BIST100 fiyat, temel/teknik metrikler ve puanlama motoru
- [ ] Phase 29: Dashboard — BIST100 özeti, döviz, altın ve portföy özeti
- [ ] Phase 30: Keşif & Hisse Detay — skorlu liste, metrik açıklamaları, on-demand AI analizi
- [ ] Phase 31: Haberler — KAP + basın birleşik haber akışı
- [ ] Phase 32: Portföy — alım-satım girişi, kâr/zarar takibi, watchlist
- [ ] Phase 33: Model Portföy — özerk haftalık model portföy ve karşılaştırma

## Performance Metrics

| Metric | v3.1 | v4.0 |
|--------|-------|-------|
| Phases | 6 | 6 (planned) |
| Plans | 7 | 14 (planned) |
| Requirements | 25/25 | 23/23 mapped |
| Started | 2026-04-28 | 2026-05-04 |
| Completed | 2026-04-29 | — |
| Phase 28-veri-altyap-s P01 | 5 | 3 tasks | 6 files |
| Phase 28-veri-altyap-s P02 | 3 | 3 tasks | 2 files |
| Phase 28-veri-altyap-s P03 | 220 | 3 tasks | 3 files |
| Phase 29-dashboard P01 | 2 | 3 tasks | 3 files |
| Phase 29-dashboard P02 | 5 | 3 tasks | 2 files |

## Accumulated Context

### Key Decisions

- On-demand AI analizi (DeepSeek) — sadece "Analiz Et" butonunda tetiklenir; API maliyeti kontrolü
- BIST100 evreni — likit, veri kaliteli, odaklı başlangıç (BIST250+ v2'ye bırakıldı)
- Giriş yok — kişisel araç, tek kullanıcı, sürtünmeyi azaltır
- Model portföy özerk — AI kendi kararlarını verir, kullanıcı karşılaştırır
- Kripto yok — odak dışı, v1 için gereksiz
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

- AI çağrıları yalnızca kullanıcı "Analiz Et" dediğinde; gereksiz çağrı yok
- Stack: Next.js (frontend, Vercel) + FastAPI (backend, Railway) + PostgreSQL
- Tamamen Türkçe arayüz
- Web-first, responsive — native app yok

### Blockers

None.

## Session Continuity

**Last session:** 2026-05-07T17:16:52.197Z
**Next action:** Execute Phase 29 (Dashboard)

---
