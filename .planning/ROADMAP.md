# Roadmap: Stalize Gerçek Veri Finansal Analiz Sistemi

## Milestones

- ✅ **v2.0 Gerçek Veri Çekirdeği** — Phases 01–16 (shipped 2026-04-27)
- ✅ **v3.0 Tüm Borsa + Kullanılabilir Platform** — Phases 17–21 (shipped 2026-04-28)

## Phases

<details>
<summary>✅ v2.0 Gerçek Veri Çekirdeği (Phases 01–16) — SHIPPED 2026-04-27</summary>

- [x] Phase 01: Foundation Repair (5 plans) — mock/fake temizlik, routing, UTC
- [x] Phase 02: ML Persistence & Caching (4 plans) — XGBoost disk, requests-cache, diskcache
- [x] Phase 03: LLM Infrastructure (4 plans) — instructor, DeepSeek (sonradan kaldırıldı)
- [x] Phase 04: AI Daily Briefing (3 plans) — APScheduler brifing (sonradan kaldırıldı)
- [x] Phase 05: UI Redesign (5 plans) — dashboard, candlestick, skor tablosu
- [x] Phase 06: Teknik Düzeltmeler (3 plans) — APScheduler, async, pandas, double-count
- [x] Phase 07: Sinyal Kalitesi (4 plans) — ATR stop-loss, hacim ratio, RSI divergence
- [x] Phase 10: Temizlik & Skor (3 plans) — AI/LLM/ML/causal kaldırma, F/45 T/40 N/15
- [x] Phase 11: Model Portföy Backend (3 plans) — ORM, snapshot job, API endpoints
- [x] Phase 12: Portföy Sayfa Skeleton (2 plans) — heatmap + karşılaştırma skeleton
- [x] Phase 13: Dashboard & Glassmorphism (3 plans) — design system, sparklines, sektör dropdown
- [x] Phase 14: Hisse Detay Yeniden Tasarım (3 plans) — CandlestickEMAPanel, FundamentalCard, KAPNewsCard
- [x] Phase 15: Portföy Tamamlama (2 plans) — BIST100 benchmark, BistComparisonChart, heatmap
- [x] Phase 16: EMA Trend Skoru (2 plans) — EMA trend bileşeni TDD, scoring integrity

Full details: `.planning/milestones/v2.0-ROADMAP.md`

</details>

<details>
<summary>✅ v3.0 Tüm Borsa + Kullanılabilir Platform (Phases 17–21) — SHIPPED 2026-04-28</summary>

- [x] Phase 17: Evren Genişlemesi (4 plans) — 399 Borsa İstanbul hissesi, rate limiting, infinite scroll
- [x] Phase 18: Hisse Sayfası Overhaul (1 plan) — TradingView, EV/EBITDA, rakip karşılaştırma, 10 KAP haberi
- [x] Phase 19: UI/UX Foundation — sistem teması auto-detect, Tarama + Watchlist nav
- [x] Phase 20: Tarama Motoru (1 plan) — /screener endpoint + frontend, 4 şablon, localStorage kaydet
- [x] Phase 21: Watchlist (1 plan) — /watchlist sayfası, hisse sayfasından toggle

Full details: `.planning/milestones/v3.0-ROADMAP.md`

</details>

## Kuzey Yıldızı

Stalize, BIST100 odaklı ama BIST'i etkileyen yerel ve küresel tüm önemli akışları izleyebilen, tamamen gerçek veriye dayalı bir analiz terminalidir. Amaç günlük trade terminali değil; özellikle 3-12 ay ufkunda daha güçlü hisse seçimi ve portföy yönetimi yaptıran bir karar sistemi kurmak.

**Temel ilkeler:**
1. Mock yok, simülasyon yok, sentetik haber yok.
2. KAP şirket verisinde birinci kaynak.
3. Kaynak önceliği ülkeye göre değil, BIST etkisine göre.
4. Dokunulan her fazda UI tutarsızlığı aynı turda düzeltilir.
5. Veri gelmiyorsa sistem boş döner; yanlış tahmin üretmez.
