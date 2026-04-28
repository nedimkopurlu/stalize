# Stalize — Borsa İstanbul Analiz Terminali

## What This Is

Stalize, BIST100 odaklı ama BIST'i etkileyen yerel ve küresel akışları birlikte okuyabilen, tamamen gerçek veriye dayalı bir finansal analiz terminalidir. Sistem teknik, temel, KAP, makro ve haber/olay verilerini tek karar yüzeyinde toplar. Veri yoksa boş döner; mock, simülasyon veya sentetik haber üretmez.

## Core Value

Gerçek ve denetlenebilir veriyle çalışan, orta ve uzun vadeli yatırım kararlarını güçlendiren bir BIST100 analiz ve portföy işletim sistemi kur.
Ana kullanım odağı: dashboard-first, hisse seçimi ve portföy yönetimi.

## Current Milestone: v4.0 — Audit Düzeltmeleri

**Başlandı:** 2026-04-28
**Fazlar:** 22–27 (6 faz)
**Gereksinimler:** 25/25 mapped

**Hedef:** Async güvenliği, endpoint auth, veri güvenilirliği, skor tutarlılığı, frontend hata yönetimi ve Python 3.12 geçişi ile sistemin denetim bulgularını gidermek.

**Aktif fazlar:**
- [ ] Phase 22: Async Infrastructure (ASYNC-01, 02, 03, 04)
- [ ] Phase 23: Security Hardening (SEC-01, 02, 03, 04)
- [ ] Phase 24: Data Reliability (DATA-01, 02, 03, 04, 05)
- [ ] Phase 25: Business Logic Correctness (LOGIC-01, 02, 03, 04)
- [ ] Phase 26: Frontend Quality (FE-01, 02, 03, 04, 05)
- [ ] Phase 27: Infrastructure Upgrade (INFRA-01, 02, 03)

## Design Philosophy

Stalize'da tasarım ayrı bir katman değil, ürün mantığının parçasıdır.

- Arayüzün tek amacı yatırım kararını hızlandırmak olacak.
- Aynı veri aynı görsel dilde sunulacak; sayfalar kendi başına farklı ürün gibi davranmayacak.
- Büyük vitrin alanları, gereksiz hero blokları ve bilgi tekrarı kabul edilmeyecek.
- Her fazda dokunulan ekranlarda bulunan tasarım tutarsızlıkları aynı iş paketinde düzeltilecek.
- Dashboard-first, sade, kurumsal ve modern bir terminal hissi korunacak.

## Investment Philosophy

Sistem beş katmanla bakar:

1. **TEMEL** — F/K, PD/DD, ROE, marjlar, borçluluk, büyüme
2. **TEKNİK** — trend, momentum, ATR, hacim, RSI, MACD, yapı
3. **ŞİRKET OLAYLARI** — KAP bildirimi, finansal sonuç, temettü, geri alım, yatırım, ihale
4. **MAKRO** — TCMB, TÜİK, HMB, emtia, faiz, döviz, piyasa rejimi
5. **HABER ETKİSİ** — resmi kaynak + yerel/global medya, etki büyüklüğüne göre sıralı

**Odak:** günlük trade sinyali değil; özellikle 3-12 ay ufkunda, gerektiğinde daha kısa veya daha uzun elde tutulabilecek daha sağlam pozisyon kararları.

## User Fit

Bu ürün şu kullanıcı profiline göre şekilleniyor:

- ana ekran olarak dashboard kullanmak isteyen
- borsa dışı bilgi kalabalığı istemeyen
- hisse seçimi, piyasa takibi ve portföy yönetimini birlikte görmek isteyen
- trade yerine orta vadeli ve uzun vadeli karar desteği arayan
- sistemin kendi haftalık model portföyünü kurmasını ama kişisel portföyünü ayrı yönetmek isteyen

## Shipped: v2.0 — Gerçek Veri Çekirdeği ✅

**Tamamlandı:** 2026-04-27 — 16 faz, 42 plan, 24/24 gereksinim

**Teslim edilenler:**
- Tüm mock/simülasyon fallback'ler temizlendi; sistem gerçek veri yoksa boş döner
- KAP + TCMB + TÜİK + HMB + Borsa İstanbul + MKK + Takasbank + TEFAS omurgası
- Explainable skor motoru (Temel %45 + Teknik %40 + Haber %15) + EMA trend bileşeni
- Haftalık model portföy sistemi (review, öz değerlendirme, değişim günlüğü, karar bandı)
- Kişisel portföy — ayrı yüzey, benchmark karşılaştırma, günlük snapshot
- Glassmorphism terminal arayüzü — dashboard, hisse detay, portföy, glassmorphism design system

## Shipped: v3.0 — Tüm Borsa + Kullanılabilir Platform ✅

**Tamamlandı:** 2026-04-28 — 5 faz, 9 plan

**Teslim edilenler:**
- BIST100 kısıtı kaldırıldı; 399 aktif Borsa İstanbul hissesi, rate limiting, hata izolasyonu
- Hisse sayfası: TradingView gömülü grafik, EV/EBITDA, rakip karşılaştırma, 10 KAP haberi
- Sistem teması auto-detect (prefers-color-scheme), manuel toggle, Tarama + Watchlist nav
- Tarama motoru: /screener endpoint + frontend, 4 hazır şablon, özelleştirilebilir builder, localStorage
- İzleme listesi: /watchlist sayfası (localStorage), hisse sayfasından toggle

## Requirements

### Validated

- ✓ FastAPI + PostgreSQL + Next.js monorepo omurgası çalışıyor — v1.0
- ✓ BIST100 veri çekimi ve temel teknik akışlar mevcut — v1.0
- ✓ KAP feed tabanlı şirket olayı altyapısı mevcut — v1.0
- ✓ Teknik sinyal katmanında ATR, hacim oranı, RSI divergence mevcut — v1.1
- ✓ AI/LLM çekirdeği kaldırıldı; pure veri analizi yeterli — v2.0
- ✓ Tüm mock/simülasyon fallback'ler kaldırıldı; gerçek veri zorunlu — v2.0
- ✓ KAP + 8 resmi kaynak ingest omurgası (TCMB, TÜİK, HMB, MKK, Takasbank, TEFAS, Borsa İstanbul) — v2.0
- ✓ Explainable skor motoru F/45 T/40 N/15 + EMA trend bileşeni — v2.0
- ✓ Haftalık model portföy + öz değerlendirme + günlük snapshot — v2.0
- ✓ Kişisel portföy ayrı yüzey + BIST100 benchmark karşılaştırma — v2.0
- ✓ Glassmorphism terminal arayüzü — dashboard, hisse detay, portföy — v2.0
- ✓ 399 aktif Borsa İstanbul hissesi; rate limiting + hata izolasyonu ile güvenli çekim — v3.0
- ✓ TradingView gömülü grafik + EV/EBITDA + rakip karşılaştırma + 10 KAP haberi — v3.0
- ✓ Sistem teması auto-detect (prefers-color-scheme), manuel toggle — v3.0
- ✓ Tarama motoru: /screener endpoint, 4 şablon, özelleştirilebilir builder, localStorage — v3.0
- ✓ İzleme listesi: localStorage tabanlı, hisse sayfasından toggle — v3.0

### Active (v4.0)

- [ ] **ASYNC-01**: `time.sleep()` → `await asyncio.sleep()` — Phase 22
- [ ] **ASYNC-02**: Tüm API route'ları `Depends(get_db)` kullanıyor — Phase 22
- [ ] **ASYNC-03**: 14 scheduler job staggered, thundering herd yok — Phase 22
- [ ] **ASYNC-04**: Startup `asyncio.create_task()` hataları sessizce kırmıyor — Phase 22
- [ ] **SEC-01**: Tüm POST/DELETE API key dependency gerektiriyor — Phase 23
- [ ] **SEC-02**: CORS wildcard yok, credentials ile CSRF vektörü kapalı — Phase 23
- [ ] **SEC-03**: API response'ları `str(e)` döndürmüyor — Phase 23
- [ ] **SEC-04**: `DEBUG=False` varsayılan, SQL echo production'da kapalı — Phase 23
- [ ] **DATA-01**: KAP symbol extraction `BIST_FULL_SYMBOLS` kullanıyor — Phase 24
- [ ] **DATA-02**: `datetime.now(timezone.utc)` data_collector'da zorunlu — Phase 24
- [ ] **DATA-03**: yfinance boş dönüş ile ağ hatası ayırt ediliyor — Phase 24
- [ ] **DATA-04**: Diskcache dizin boyutu sınırlı — Phase 24
- [ ] **DATA-05**: `NewsItem(source, url)` unique constraint DB seviyesinde — Phase 24
- [ ] **LOGIC-01**: İki scoring fonksiyonu aynı ağırlıkları kullanıyor — Phase 25
- [ ] **LOGIC-02**: Screener geçersiz aralıkları HTTP 400 ile reddediyor — Phase 25
- [ ] **LOGIC-03**: ATR volatilite teknik skorda bileşen olarak aktif — Phase 25
- [ ] **LOGIC-04**: Portfolio P&L eksik fiyatları `partial: true` ile işaretliyor — Phase 25
- [ ] **FE-01**: Boş `catch(() => {})` kaldırıldı, hata UI'ı görünüyor — Phase 26
- [ ] **FE-02**: `MacroPanel` unsafe type assertion düzeltildi — Phase 26
- [ ] **FE-03**: Screener `api.ts` helper kullanıyor — Phase 26
- [ ] **FE-04**: Portfolio formu client-side validation yapıyor — Phase 26
- [ ] **FE-05**: Yıkıcı aksiyonlar onay dialogu gösteriyor — Phase 26
- [ ] **INFRA-01**: Python 3.9 → 3.12 yükseltmesi — Phase 27
- [ ] **INFRA-02**: `/health` endpoint DB bağlantısını test ediyor — Phase 27
- [ ] **INFRA-03**: Emoji'siz structured logging — Phase 27

### Out of Scope

| Feature | Reason |
|---------|--------|
| Otomatik emir iletimi | Sistem karar desteği verir, emir vermez |
| Multi-user erişim | Kişisel kullanım |
| OAuth / kayıt sistemi | Gerek yok |
| Mobil uygulama | Web-first |
| AI/LLM briefing | Kaldırıldı — pure veri analizi yeterli (v2.0) |
| Causal knowledge graph | Kaldırıldı — kullanılmıyor, karmaşıklık ekliyor (v2.0) |
| XGBoost fiyat tahmini | Kaldırıldı — veri yetersizliği, güvenilmez (v2.0) |
| Simülasyon/backtesting çıktısı | Gerçek veri dışında kabul yok |
| Operasyonel debug panellerinin ana dashboard'da görünmesi | Son kullanıcı odağına hizmet etmiyor |
| Glassmorphism CSS kaldırma | Kullanıcı mevcut tasarımı onayladı (v4.0) |
| Watchlist backend persistence | localStorage v4.0 için yeterli (v4.0) |
| Otomatik BIST universe güncelleme | Statik liste yılda 1-2 güncelleme yeterli (v4.0) |
| Test coverage arttırma | Mevcut test suite korunuyor (v4.0) |

## Context

**v4.0 başlangıç durumu (2026-04-28):**
- 21 faz toplam (v2.0 + v3.0), 51 plan
- v4.0: 6 faz (22–27), 25 gereksinim, planlar henüz başlatılmadı
- Backend: FastAPI + SQLAlchemy async + PostgreSQL
- Frontend: Next.js App Router; screener + watchlist sayfaları, TradingView iframe, infinite scroll
- Stock model: is_bist250 + market_tier kolonları; alembic migration 003
- TypeScript sıfır hata

**Altyapı:**
- FastAPI + SQLAlchemy async + PostgreSQL
- Next.js frontend (App Router)
- APScheduler arka plan işleri
- KAP parser, portföy snapshot omurgası, EMA teknik analiz motoru

**Aktif veri kaynakları:**
- 1. KAP (şirket bildirimleri — birincil)
- 2. Resmi kurumlar: Borsa İstanbul, TCMB, TÜİK, HMB, MKK, Takasbank, TEFAS (9 aktif)
- 3. Global + yerel haber: Reuters, Bloomberg, FT, CNBC, Investing, BloombergHT, Ekonomim, Dunya

**Teknik borç (v4.0 için — aktif çalışma):**
- Pydantic V2 ConfigDict geçişi
- Watchlist backend persistence yok (localStorage only — v4.0 kapsamı dışı)
- Screener performance optimization (500 hisse sub-query join)
- Makro parser kalibrasyon (TCMB/TÜİK kırılgan uçlar)

## Constraints

- **Gerçek veri zorunlu**: mock, simülasyon, sentetik olay yok
- **Kaynak önceliği**: ülkeye göre değil, BIST etkisine göre; şirket olayında KAP birinci
- **LLM yok**: sistem kural tabanlı ve veri tabanlı çalışır
- **Python**: 3.12 (v4.0 sonrası)
- **Çalışma ortamı**: lokal geliştirme, localhost servisleri

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| AI/LLM kaldır | güvenilir veri çekirdeğine odak | ✓ v2.0 tamamlandı |
| KAP birincil kaynak | şirket etkisini en doğru yerden almak | ✓ aktif ilke |
| Impact-first kaynak stratejisi | BIST'i etkileyen haber ülke fark etmeksizin önemli | ✓ aktif ilke |
| Simülasyon yasak | veri gelmiyorsa boş dönmek daha güvenli | ✓ aktif ilke |
| Önce veri güvenilirliği, sonra UI | yanlış verinin güzel görünmesi değer üretmez | ✓ aktif ilke |
| Dashboard-first sade UX | kullanıcı önce hisse seçimi ve piyasa odağını görmeli | ✓ aktif ilke |
| Haftalık model portföy | sistem sadece analiz değil, haftalık karar masası da sunmalı | ✓ v2.0 tamamlandı |
| Model portföy öz değerlendirme | sistem geçen haftanın zayıflığını okuyup sonraki haftada adapte olmalı | ✓ v2.0 tamamlandı |
| Ayrı kişisel portföy | kullanıcının gerçek portföyü sistem portföyünden ayrı yönetilmeli | ✓ v2.0 tamamlandı |
| Faz içi tasarım temizliği | teknik ilerleme sırasında görülen UI tutarsızlığı ertelenmez | ✓ aktif ilke |
| EMA 50/200 blend (60/40) | orta vadeli trend sinyalini teknik skora yansıt | ✓ v2.0 tamamlandı |
| Glassmorphism terminal | koyu tema, sade, kurumsal operatör terminali hissi | ✓ v2.0 tamamlandı |
| bist_full_universe.py statik liste | yılda 1-2 güncelleme yeterli, otomatik discovery karmaşıklık ekliyor | ✓ v3.0 tamamlandı |
| Watchlist localStorage tabanlı | backend gerektirmiyor, kişisel kullanım için yeterli | ✓ v3.0 tamamlandı |
| TradingView iframe embed | free widget, BIST:SYMBOL format çalışıyor, sıfır bakım | ✓ v3.0 tamamlandı |
| Screener iki aşamalı (SQL + Python) | SQL hız + Python esnekliği; Fundamental join karmaşıklığını azaltır | ✓ v3.0 tamamlandı |
| Glassmorphism CSS korunuyor | kullanıcı mevcut tasarımı onayladı; kaldırma v4.0 kapsamı dışı | ✓ v4.0 kararı |
| Python 3.12 geçişi | 3.9 EOL; Railway uyumu ve güncel ekosistem | v4.0 Phase 27 |

---
*Last updated: 2026-04-28 — v4.0 milestone başlatıldı (6 faz, 25 gereksinim)*
