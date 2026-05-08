# Roadmap: Stalize Gerçek Veri Finansal Analiz Sistemi

## Milestones

- ✅ **v2.0 Gerçek Veri Çekirdeği** — Phases 01–16 (shipped 2026-04-27)
- ✅ **v3.0 Tüm Borsa + Kullanılabilir Platform** — Phases 17–21 (shipped 2026-04-28)
- ✅ **v3.1 Audit Düzeltmeleri** — Phases 22–27 (shipped 2026-04-29)
- ✅ **v4.0 Kişisel Yatırım Asistanı** — Phases 28–29 (completed); Phases 30–33 absorbed into v5.0
- 🚧 **v5.0 LLM Entegrasyonlu Yatırım Asistanı** — Phases 34–39 (aktif)

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

<details>
<summary>✅ v3.1 Audit Düzeltmeleri (Phases 22–27) — SHIPPED 2026-04-29</summary>

- [x] Phase 22: Async Infrastructure — Event loop ve bağlantı havuzu sağlığı ✅
- [x] Phase 23: Security Hardening — Endpoint auth, CORS, hata sanitizasyonu ✅
- [x] Phase 24: Data Reliability — KAP sembol kapsamı, datetime doğruluğu, cache sınırları ✅
- [x] Phase 25: Business Logic Correctness — Skor tutarlılığı, screener validasyonu, volatilite ✅
- [x] Phase 26: Frontend Quality — Hata görünürlüğü, tip güvenliği, form validasyonu ✅
- [x] Phase 27: Infrastructure Upgrade — Python 3.12, health endpoint, structured logging ✅

Full details: See Phase Details section (archived phases 22–27 inline above).

</details>

<details>
<summary>✅ v4.0 Kişisel Yatırım Asistanı (Phases 28–29) — COMPLETED; Phases 30–33 absorbed into v5.0</summary>

- [x] **Phase 28: Veri Altyapısı** — BIST100 odaklı fiyat, temel/teknik metrikler ve puanlama motorunun hazırlanması (completed 2026-05-05)
- [x] **Phase 29: Dashboard** — BIST100 özeti, döviz, altın ve portföy özetinin tek ekranda görünmesi (completed 2026-05-07)

Phases 30–33 (Keşif, Haberler, Portföy, Model Portföy) planned in v4.0 but never executed — scope absorbed into v5.0 with Gemini LLM integration.

</details>

### v5.0 LLM Entegrasyonlu Yatırım Asistanı (Phases 34–39) — AKTİF

**Milestone Hedefi:** Gemini 2.0 Flash ile LLM entegrasyonu ekle; prototype tasarımına tam uyum sağla; tüm eksik sayfaları (Keşif, Haberler, Portföy, Model Portföy) tamamla.

- [x] **Phase 34: Frontend Tasarım Düzeltmeleri** — Prototype audit sonrası bulunan 6 tasarım tutarsızlığı giderilir (completed 2026-05-08)
- [ ] **Phase 35: Gemini LLM Altyapısı** — Backend Gemini 2.0 Flash servis katmanı kurulur; quota aşımında graceful fallback çalışır
- [ ] **Phase 36: Keşif & Hisse Detay + AI Analizi** — Skorlu hisse listesi, detay sayfası (metrik tooltipli), on-demand Gemini analizi
- [ ] **Phase 37: Haberler + Günlük Piyasa Özeti** — KAP + basın birleşik haber akışı; her sabah otomatik Gemini piyasa özeti
- [ ] **Phase 38: Portföy** — Alım-satım girişi, P&L takibi, BIST100 karşılaştırması, watchlist
- [ ] **Phase 39: Model Portföy + AI Kararları** — Özerk haftalık model portföy; Gemini Türkçe gerekçe; karar geçmişi; kullanıcı karşılaştırması

## Phase Details

### Phase 22: Async Infrastructure
**Goal**: Servis, yük altında event loop'u bloke etmeden ve bağlantı havuzunu sızdırmadan çalışıyor.
**Depends on**: Nothing (first v3.1 phase)
**Requirements**: ASYNC-01, ASYNC-02, ASYNC-03, ASYNC-04
**Success Criteria** (what must be TRUE):
  1. Yfinance retry sırasında diğer API request'leri yanıt vermeye devam ediyor; `time.sleep()` kodu artık yok.
  2. API route'larının hiçbirinde `AsyncSessionLocal()` doğrudan çağrısı yok; tüm DB erişimi `Depends(get_db)` üzerinden geçiyor.
  3. 14 scheduler job aynı anda tetiklenmiyor; ardışık başlatma ile thundering herd gözlemlenmiyor.
  4. Uygulama başlatıldığında bir `asyncio.create_task()` hatası oluşursa servis sessizce kırık başlamıyor; hata log'da görünüyor ve health durumuna yansıyor.
**Plans**: 2 plans

Plans:
- [x] 22-01-PLAN.md — Sleep fix (data_collector, macro_news) + session migration (stocks, portfolio_v2, macro, admin) to Depends(get_db)
- [x] 22-02-PLAN.md — Scheduler job staggering with start_date offsets + asyncio startup task error tracking

### Phase 23: Security Hardening
**Goal**: Tüm mutasyon endpoint'leri kimlik doğrulaması gerektiriyor ve API response'ları iç hata detaylarını sızdırmıyor.
**Depends on**: Phase 22
**Requirements**: SEC-01, SEC-02, SEC-03, SEC-04
**Success Criteria** (what must be TRUE):
  1. API key olmadan hiçbir POST veya DELETE endpoint'i başarılı dönmüyor; kimlik doğrulamasız istek HTTP 401/403 alıyor.
  2. CORS konfigürasyonu wildcard origin içermiyor; yalnızca izin verilen origin'ler kabul ediliyor.
  3. Bir endpoint hata fırlatırsa istemci `str(e)` değil generic bir hata mesajı görüyor; detaylı hata yalnızca server log'da görünüyor.
  4. Uygulama varsayılan olarak `DEBUG=False` ve SQL echo kapalı başlıyor; env var ile override edilebiliyor.
**Plans**: 1 plan

Plans:
- [x] 23-01-PLAN.md — Security hardening

### Phase 24: Data Reliability
**Goal**: Sistem, veri toplama sırasında yanlış zaman damgası üretmiyor, cache'i sınırsız büyütmüyor ve aynı bildirimi çoğaltmıyor.
**Depends on**: Phase 22
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05
**Success Criteria** (what must be TRUE):
  1. BIST250+ kapsamındaki şirketlerin KAP haberleri sisteme giriyor; symbol extraction `BIST_FULL_SYMBOLS` listesini kullanıyor.
  2. Data collector'daki tüm `datetime.now()` çağrıları UTC-aware; naive datetime UTC karşılaştırmasını kırmıyor.
  3. Yfinance'tan boş dönüş ile ağ hatası log'da ayrı mesajlarla ayırt ediliyor; başarısız semboller `SourceHealthRun` tablosuna yazılıyor.
  4. Diskcache dizini disk kullanımı sınırlı; Railway ortamında sınırsız büyüme olmuyor.
  5. Aynı (source, url) çiftine sahip bir KAP bildirimi tekrar ingest edildiğinde DB'ye ikinci kayıt eklenmiyor; unique constraint ihlali sessizce yutulmuyor.
**Plans**: 1 plan

Plans:
- [x] 24-01-PLAN.md — Data reliability fixes

### Phase 25: Business Logic Correctness
**Goal**: Skor hesaplama tutarlı, screener geçersiz girdileri reddediyor ve portföy P&L eksik fiyatları işaretliyor.
**Depends on**: Phase 24
**Requirements**: LOGIC-01, LOGIC-02, LOGIC-03, LOGIC-04
**Success Criteria** (what must be TRUE):
  1. Aynı hisse için `calculate_overall_score()` ve `get_contextual_score_breakdown()` aynı ağırlıkları kullanıyor; API'nin öneri ve breakdown alanları çelişmiyor.
  2. Screener'a `pe_ratio_min > pe_ratio_max` gibi geçersiz aralık gönderildiğinde HTTP 400 dönüyor; boş sonuç listesi ile sessizce geçmek yerine hata açık.
  3. ATR volatilite bileşeni teknik skorda aktif; yüksek volatiliteli hisse ile düşük volatiliteli hisse aynı teknik puanı almıyor.
  4. Portföy P&L response'unda fiyat alınamayan pozisyonlar `partial: true` ile işaretlenmiş olarak dönüyor.
**Plans**: 1 plan

Plans:
- [x] 25-01-PLAN.md — Business logic correctness

### Phase 26: Frontend Quality
**Goal**: Tüm sayfalarda hata durumları kullanıcıya görünür; yıkıcı aksiyonlar onay gerektiriyor.
**Depends on**: Phase 25
**Requirements**: FE-01, FE-02, FE-03, FE-04, FE-05
**Success Criteria** (what must be TRUE):
  1. Herhangi bir sayfada API hatası oluştuğunda kullanıcı boş ekran yerine hata mesajı görüyor; `catch(() => {})` bloğu yok.
  2. `MacroPanel` bileşeninde `asOfKey` unsafe type assertion kaldırılmış; TypeScript build sıfır hata üretiyor.
  3. Screener sayfası tüm fetch işlemlerini `api.ts` üzerinden yapıyor; hata durumunda UI hata gösteriyor.
  4. Portföy formu `entry_price <= 0` veya `quantity <= 0` gönderildiğinde server'a istek atmadan client-side hata gösteriyor.
  5. Pozisyon kapatma ve watchlist'ten çıkarma aksiyonları onay dialogu gösterdikten sonra gerçekleşiyor.
**Plans**: 1 plan

Plans:
- [x] 26-01-PLAN.md — Frontend quality

### Phase 27: Infrastructure Upgrade
**Goal**: Servis Python 3.12 üzerinde çalışıyor, sağlık durumu gerçek DB bağlantısını yansıtıyor ve log'lar makine tarafından parse edilebilir.
**Depends on**: Phase 22
**Requirements**: INFRA-01, INFRA-02, INFRA-03
**Success Criteria** (what must be TRUE):
  1. Backend Python 3.12 ile başarıyla başlıyor; tüm bağımlılıklar 3.12-compatible; 3.9'a özgü sözdizimi yok.
  2. `/health` endpoint'i DB'ye gerçek bağlantı testi yapıyor; DB düşükse endpoint başarısız (non-200) dönüyor.
  3. Uygulama log'ları emoji içermiyor ve structured format kullanıyor; kritik job hataları log'da aranabilir durumda.
**Plans**: 1 plan

Plans:
- [x] 27-01-PLAN.md — Infrastructure upgrade

### Phase 28: Veri Altyapısı
**Goal**: BIST100 hisselerinin fiyatları, temel metrikleri, teknik göstergeleri ve birleşik fırsat skoru API'den erişilebilir hâlde; döviz ve altın fiyatları da dahil.
**Depends on**: Phase 27
**Requirements**: DASH-01, DASH-02, DASH-03, DISC-01, DISC-02
**Success Criteria** (what must be TRUE):
  1. API, BIST100 endeksinin günlük değişimini ve hacmini döndürür
  2. API, 5-10 döviz çiftini ve altının beş formunu (gram, ons, çeyrek, yarım, tam) döndürür
  3. Her BIST100 hissesi için temel metrikler (F/K, PD/DD, net kar, bilanço büyümesi) veritabanında saklanır ve API üzerinden alınabilir
  4. Her BIST100 hissesi için teknik göstergeler (RSI, MACD, hareketli ortalamalar) hesaplanır
  5. Temel + teknik skorlar birleştirilerek her hisse için tek bir fırsat skoru üretilir; en yüksek skorlular listelenebilir
**Plans**: 3 plans

Plans:
- [x] 28-01-PLAN.md — Foundation: market.py router skeleton + JPY/CHF forex config + RED test scaffolds
- [x] 28-02-PLAN.md — /market/bist100, /market/forex, /market/gold endpoints (DASH-01, DASH-02, DASH-03)
- [x] 28-03-PLAN.md — /market/opportunities + DISC-01 verification (DISC-01, DISC-02)

### Phase 29: Dashboard
**Goal**: Kullanıcı uygulamayı açtığında piyasanın nabzını (BIST100, döviz, altın) ve kendi portföy özetini tek sayfada görür.
**Depends on**: Phase 28
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04
**Success Criteria** (what must be TRUE):
  1. Kullanıcı BIST100 endeksinin günlük değişimini ve hacmini dashboard'da görür
  2. Kullanıcı 5-10 döviz çiftini (USD/TRY, EUR/TRY, GBP/TRY dahil) canlı fiyatlarıyla görür
  3. Kullanıcı altın fiyatlarını (gram, ons, çeyrek, yarım, tam) görür
  4. Kullanıcı portföyünün toplam değerini ve günlük değişimini özet olarak görür (portföy boşsa boş durum gösterir)
**Plans**: 2 plans

Plans:
- [x] 29-01-PLAN.md — api.ts market endpoints + page.tsx/page.module.css rewrite (BIST100 banner, Döviz, Altın widgets, 30s auto-refresh)
- [x] 29-02-PLAN.md — Portfolio placeholder per UI-SPEC (Henüz portföy eklenmedi) + browser smoke checkpoint

### Phase 34: Frontend Tasarım Düzeltmeleri
**Goal**: Kullanıcı prototype'a tam uyumlu bir arayüzle çalışır; 6 tespit edilen görsel tutarsızlık giderilir.
**Depends on**: Phase 29
**Requirements**: DESIGN-01, DESIGN-02, DESIGN-03, DESIGN-04, DESIGN-05, DESIGN-06
**Success Criteria** (what must be TRUE):
  1. Dashboard BIST100 grafiği 6 periyot tabını gösterir (1G, 1H, 1A, 3A, 1Y, Tüm); intraday verisi yoksa mock veri ile sekme çalışır durumda kalır
  2. Kazananlar/kaybedenler satırlarında 40×28px mini sparkline prototype'a uygun şekilde görünür
  3. Model portföy sayfası 6 strateji kartını (Temettü Avcısı, Büyüme Lokomotifleri, Defansif Kalkan dahil) listeler
  4. Light mode'da hover durumları hardcoded renk değeri yerine theme-aware CSS değişkeni kullanır; karanlık arka plan artifaktı görünmez
  5. Dashboard portföy kartı pozisyon yokken "/portföy" sayfasına yönlendiren Türkçe boş durum mesajı gösterir; `SparklineWidget.tsx` ve kullanılmayan api.ts metodları kod tabanında bulunmaz
**Plans**: TBD

Plans:
- [x] 34-01: BIST100 grafik 6 tab + sparkline düzeltmesi (DESIGN-01, DESIGN-02)
- [x] 34-02: Model portföy 6 kart + hover fix + dead code temizlik + portföy boş durum (DESIGN-03, DESIGN-04, DESIGN-05, DESIGN-06)

### Phase 35: Gemini LLM Altyapısı
**Goal**: Backend'de Gemini 2.0 Flash servis katmanı çalışır; tüm LLM çağrıları bu katmandan geçer ve quota aşımında sistem hata yerine placeholder döner.
**Depends on**: Phase 34
**Requirements**: LLM-01
**Success Criteria** (what must be TRUE):
  1. `google-generativeai` SDK ile Gemini 2.0 Flash'a istek gönderilebilir; API key `.env`'den okunur
  2. Quota aşıldığında (429) endpoint HTTP 500 yerine yapılandırılmış bir fallback mesajı döner; uygulama çökmez
  3. Servis katmanı izole edilmiş bir modül olarak import edilebilir; tüm üst-level LLM çağrıları bu modülden geçer
**Plans**: TBD

Plans:
- [ ] 35-01: GeminiService sınıfı — SDK entegrasyonu, async generate, quota fallback, unit testler

### Phase 36: Keşif & Hisse Detay + AI Analizi
**Goal**: Kullanıcı yüksek fırsatlı hisseleri keşfeder, detay sayfasında tüm metrikleri Türkçe açıklamalarıyla görür ve talep üzerine Gemini'den Türkçe analiz alır.
**Depends on**: Phase 35
**Requirements**: DISC-03, STCK-01, STCK-02, STCK-03, STCK-04, STCK-05, STCK-06, LLM-02
**Success Criteria** (what must be TRUE):
  1. Kullanıcı keşif sayfasında BIST100 hisselerini skora göre sıralar; bir hisseye tıkladığında detay sayfasına gider
  2. Detay sayfasında fiyat grafiği 4 zaman aralığında görünür (7g, 1ay, 3ay, 1y)
  3. Temel metrikler (F/K, PD/DD, net kar, bilanço büyümesi) ve teknik göstergeler (RSI, MACD, hareketli ortalamalar) her birinin yanında Türkçe tooltip açıklamasıyla görünür
  4. Kullanıcı "Analiz Et" butonuna bastığında Gemini o hisseye özel Türkçe analiz üretir; aynı oturumda ikinci kez basılmadan yeni istek gönderilmez
  5. Kullanıcı detay sayfasında hissenin KAP açıklamalarını ve basın haberlerini görür
**Plans**: TBD

Plans:
- [ ] 36-01: Keşif sayfası — skorlu hisse listesi, filtreleme ve sıralama (DISC-03)
- [ ] 36-02: Hisse detay — fiyat grafiği, temel ve teknik metrik kartları (Türkçe tooltipli) (STCK-01, STCK-02, STCK-03, STCK-05, STCK-06)
- [ ] 36-03: On-demand Gemini analizi — "Analiz Et" butonu, önbellek, fallback (STCK-04, LLM-02)

### Phase 37: Haberler + Günlük Piyasa Özeti
**Goal**: Kullanıcı tüm BIST haberlerini tarih sıralı tek sayfada takip eder; her sabah Gemini tarafından üretilen günlük piyasa özeti sayfanın üstünde görünür.
**Depends on**: Phase 35
**Requirements**: NEWS-01, LLM-03
**Success Criteria** (what must be TRUE):
  1. Kullanıcı haberler sayfasında KAP açıklamaları ve basın haberlerinin tarih sıralı birleşik akışını görür
  2. Sayfa yenilendiğinde yeni haberler listenin başına eklenir; eski haberler aşağıda kalır
  3. Sayfanın en üstünde o güne ait Gemini piyasa özeti kartı görünür; kart tarihi ve oluşturulma saati içerir
  4. APScheduler her sabah otomatik olarak yeni özeti üretir; kullanıcı müdahalesi gerekmez
**Plans**: TBD

Plans:
- [ ] 37-01: Haberler sayfası — KAP + basın birleşik akışı, tarih sıralı (NEWS-01)
- [ ] 37-02: Günlük Gemini piyasa özeti — APScheduler job, DB kaydı, dashboard + haberler entegrasyonu (LLM-03)

### Phase 38: Portföy
**Goal**: Kullanıcı gerçek alım-satımlarını girer, kâr/zarar takibi yapar, BIST100 ile karşılaştırır ve izleme listesi tutar.
**Depends on**: Phase 29
**Requirements**: PORT-01, PORT-02, PORT-03, PORT-04, PORT-05
**Success Criteria** (what must be TRUE):
  1. Kullanıcı hisse, lot, fiyat ve tarih girerek alım işlemi kaydeder; kayıt anında portföy listesine yansır
  2. Kullanıcı satım işlemi girer; kapalı pozisyon gerçekleşen kâr/zararla (TL ve %) görünür
  3. Kullanıcı açık pozisyonlarını güncel fiyatla hesaplanmış TL ve % kâr/zarar olarak görür
  4. Kullanıcı portföy performansını BIST100 endeksiyle grafiksel olarak karşılaştırır (aynı başlangıç tarihinden itibaren)
  5. Kullanıcı izleme listesine hisse ekler ve çıkarır; watchlist canlı fiyatlarla görünür
**Plans**: TBD

Plans:
- [ ] 38-01: Portföy veri modeli ve alım-satım işlem girişi (PORT-01, PORT-02)
- [ ] 38-02: Portföy performans görünümü ve BIST100 karşılaştırması (PORT-03, PORT-04)
- [ ] 38-03: İzleme listesi (watchlist) — ekleme, çıkarma, canlı fiyat (PORT-05)

### Phase 39: Model Portföy + AI Kararları
**Goal**: Sistem haftalık özerk model portföy yönetir; her karar Gemini tarafından Türkçe gerekçesiyle yazılır; kullanıcı geçmişi ve kendi portföyüyle karşılaştırmayı görür.
**Depends on**: Phase 35, Phase 38
**Requirements**: MODEL-01, MODEL-02, MODEL-03, MODEL-04, LLM-04
**Success Criteria** (what must be TRUE):
  1. APScheduler haftalık olarak BIST100 evreni içinde model portföyü günceller; insan müdahalesi olmadan çalışır
  2. Her alım/satım kararı Gemini'nin yazdığı Türkçe gerekçesiyle birlikte tarih damgalı olarak veritabanına kaydedilir
  3. Kullanıcı model portföyün tam geçmişini (tarih, işlem, gerekçe) sayfalanmış olarak görür
  4. Kullanıcı kendi portföyünün performansını model portföyle yan yana karşılaştırır (getiri, grafik)
**Plans**: TBD

Plans:
- [ ] 39-01: Model portföy özerk karar döngüsü + Gemini Türkçe gerekçe kaydı (MODEL-01, MODEL-02, LLM-04)
- [ ] 39-02: Model portföy görünümü — geçmiş ve kullanıcı portföyü karşılaştırması (MODEL-03, MODEL-04)

## Progress Table

**Execution Order:**
v5.0 phases execute in numeric order: 34 → 35 → 36 → 37 → 38 → 39
Note: Phase 38 depends on Phase 29 (not 35); Phase 37 depends on Phase 35; Phases 36 and 37 can execute in parallel after Phase 35.

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 22. Async Infrastructure | v3.1 | 2/2 | Complete | 2026-04-29 |
| 23. Security Hardening | v3.1 | 1/1 | Complete | 2026-04-28 |
| 24. Data Reliability | v3.1 | 1/1 | Complete | 2026-04-28 |
| 25. Business Logic Correctness | v3.1 | 1/1 | Complete | 2026-04-28 |
| 26. Frontend Quality | v3.1 | 1/1 | Complete | 2026-04-28 |
| 27. Infrastructure Upgrade | v3.1 | 1/1 | Complete | 2026-04-29 |
| 28. Veri Altyapısı | v4.0 | 3/3 | Complete | 2026-05-05 |
| 29. Dashboard | v4.0 | 2/2 | Complete | 2026-05-07 |
| 34. Frontend Tasarım Düzeltmeleri | v5.0 | 2/2 | Complete   | 2026-05-08 |
| 35. Gemini LLM Altyapısı | v5.0 | 0/1 | Not started | - |
| 36. Keşif & Hisse Detay + AI Analizi | v5.0 | 0/3 | Not started | - |
| 37. Haberler + Günlük Piyasa Özeti | v5.0 | 0/2 | Not started | - |
| 38. Portföy | v5.0 | 0/3 | Not started | - |
| 39. Model Portföy + AI Kararları | v5.0 | 0/2 | Not started | - |

## Kuzey Yıldızı

Stalize, BIST100 odaklı ama BIST'i etkileyen yerel ve küresel tüm önemli akışları izleyebilen, tamamen gerçek veriye dayalı bir analiz terminalidir. Amaç günlük trade terminali değil; özellikle 3-12 ay ufkunda daha güçlü hisse seçimi ve portföy yönetimi yaptıran bir karar sistemi kurmak.

**Temel ilkeler:**
1. Mock yok, simülasyon yok, sentetik haber yok.
2. KAP şirket verisinde birinci kaynak.
3. Kaynak önceliği ülkeye göre değil, BIST etkisine göre.
4. Dokunulan her fazda UI tutarsızlığı aynı turda düzeltilir.
5. Veri gelmiyorsa sistem boş döner; yanlış tahmin üretmez.
