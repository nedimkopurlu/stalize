# Milestones: Stalize

## v2.0 — Gerçek Veri Çekirdeği

**Shipped:** 2026-04-27
**Phases:** 16 (01, 02, 03, 04, 05, 06, 07, 10, 11, 12, 13, 14, 15, 16)
**Plans:** 42
**Requirements:** 24/24 v1.2 ✓

### Delivered

Sistemdeki tüm mock/simülasyon fallback'ler kaldırıldı. KAP + 8 resmi kaynak omurgası, explainable skor motoru, haftalık model portföy sistemi ve glassmorphism terminal arayüzü tamamlandı.

### Key Accomplishments

1. **Gerçek Veri Zorunluluğu** — Tüm mock, simulated, fake, dummy fallback'ler kaldırıldı; yfinance, KAP, TCMB gibi resmi kaynaklar olmadan sistem boş döner
2. **Resmi Kaynak Omurgası** — KAP + Borsa İstanbul + TCMB + TÜİK + HMB + MKK + Takasbank + TEFAS ingest pipeline tamamlandı (9 aktif kaynak)
3. **Explainable Skor Motoru** — Temel %45 + Teknik %40 + Haber %15; EMA 50/200 trend bileşeni (TDD, 17/17 test) eklendi; contextual breakdown ile scoring.py yeniden yazıldı
4. **Model Portföy İşletim Sistemi** — Haftalık model portföy, öz değerlendirme, değişim günlüğü, karar bandı ve günlük snapshot; kişisel portföy ayrı yüzeyde BIST100 benchmark ile karşılaştırmalı
5. **Glassmorphism Terminal Arayüzü** — Dashboard, hisse detay, hisse listesi ve portföy sayfaları ortak design system ile yeniden tasarlandı; CandlestickEMAPanel (EMA50/200 overlay + hacim + RSI), FundamentalMetricCard, KAPNewsCard, BistComparisonChart
6. **AI/LLM/ML Temizliği** — DeepSeek, causal graph, XGBoost, mock portfolio tamamen kaldırıldı; scoring pure veri tabanlı hale getirildi

### Stats

- Backend: ~730K satır Python | Frontend: ~4.6K satır TypeScript
- Active routes: 57 | Tests: 17/17 | TypeScript: 0 errors
- Timeline: 2026-04-16 → 2026-04-27

### Archive

- Roadmap: `.planning/milestones/v2.0-ROADMAP.md`
- Requirements: `.planning/milestones/v2.0-REQUIREMENTS.md`
- Audit: `.planning/milestones/v2.0-MILESTONE-AUDIT.md`

---

## v3.0 — Tüm Borsa + Kullanılabilir Platform

**Shipped:** 2026-04-28
**Phases:** 5 (17–21)
**Plans:** 9

### Delivered

BIST100 kısıtı kaldırıldı; tüm aktif Borsa İstanbul hisseleri platforma alındı. Her hisse için TradingView grafik, rakip karşılaştırma, EV/EBITDA eklendi. Çok boyutlu tarama motoru ve localStorage tabanlı izleme listesi tamamlandı.

### Key Accomplishments

1. **Evren Genişlemesi** — 399 aktif Borsa İstanbul hissesi; batch 10/1s rate limiting, hata izolasyonu; is_bist250 + market_tier kolonları; alembic migration 003
2. **Hisse Sayfası Overhaul** — TradingView gömülü grafik (BIST:SYMBOL, dark); EV/EBITDA; rakip karşılaştırma tablosu (/peers endpoint); 10 KAP haberi
3. **Sistem Teması** — prefers-color-scheme auto-detect; manuel toggle; Tarama + İzleme Listesi nav öğeleri; branding güncellendi
4. **Tarama Motoru** — /screener endpoint (SQL + Python iki aşamalı); 4 hazır şablon; özelleştirilebilir builder; localStorage kaydet/yükle; sıralanabilir sonuç tablosu
5. **İzleme Listesi** — /watchlist sayfası (localStorage); hisse sayfasından ☆/★ toggle; canlı fiyat + skor + öneri

### Stats

- v3.0: 5 faz, 9 plan
- Yeni sayfalar: /screener, /watchlist
- Yeni endpoint'ler: /screener, /stocks/{symbol}/peers
- TypeScript: 0 hata
- Timeline: 2026-04-28

### Archive

- Roadmap: `.planning/milestones/v3.0-ROADMAP.md`
- Requirements: `.planning/milestones/v3.0-REQUIREMENTS.md`

---

*Ready for next milestone: `/gsd:new-milestone`*
