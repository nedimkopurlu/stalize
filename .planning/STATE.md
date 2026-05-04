---
gsd_state_version: 1.0
milestone: v4.0
milestone_name: Kişisel Yatırım Asistanı
status: planning
last_updated: "2026-05-04T00:00:00.000Z"
progress:
  total_phases: 6
  completed_phases: 0
  total_plans: 14
  completed_plans: 0
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-05-04)

**Core value:** Kullanıcının "bu hisseyi neden almalıyım?" sorusuna hem veriyle hem açıklamayla cevap vermek — karar kullanıcıda, anlayış asistanda.
**Current milestone:** v4.0 — Kişisel Yatırım Asistanı
**Previous milestone:** v3.1 — Audit Düzeltmeleri (tamamlandı 2026-04-29)

## Current Position

**Active phase:** Phase 28 — Veri Altyapısı (ready to plan)
**Active plan:** None
**Status:** Ready to plan

```
Progress: ░░░░░░░░░░░░░░░░░░░░ 0/6 phases (v4.0)
```

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

## Accumulated Context

### Key Decisions

- On-demand AI analizi (DeepSeek) — sadece "Analiz Et" butonunda tetiklenir; API maliyeti kontrolü
- BIST100 evreni — likit, veri kaliteli, odaklı başlangıç (BIST250+ v2'ye bırakıldı)
- Giriş yok — kişisel araç, tek kullanıcı, sürtünmeyi azaltır
- Model portföy özerk — AI kendi kararlarını verir, kullanıcı karşılaştırır
- Kripto yok — odak dışı, v1 için gereksiz

### Known Constraints

- AI çağrıları yalnızca kullanıcı "Analiz Et" dediğinde; gereksiz çağrı yok
- Stack: Next.js (frontend, Vercel) + FastAPI (backend, Railway) + PostgreSQL
- Tamamen Türkçe arayüz
- Web-first, responsive — native app yok

### Blockers

None.

## Session Continuity

**Last session:** 2026-05-04 — v4.0 roadmap oluşturuldu. 23/23 gereksinim 6 faza eşlendi.
**Next action:** `/gsd:plan-phase 28`

---
