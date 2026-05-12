# Roadmap: Stalize Gerçek Veri Finansal Analiz Sistemi

## Milestones

- ✅ **v2.0 Gerçek Veri Çekirdeği** — Phases 01–16 (shipped 2026-04-27)
- ✅ **v3.0 Tüm Borsa + Kullanılabilir Platform** — Phases 17–21 (shipped 2026-04-28)
- ✅ **v3.1 Audit Düzeltmeleri** — Phases 22–27 (shipped 2026-04-29)
- ✅ **v4.0 Kişisel Yatırım Asistanı** — Phases 28–29 (completed); Phases 30–33 absorbed into v5.0
- ✅ **v5.0 LLM Entegrasyonlu Yatırım Asistanı** — Phases 34–39 (completed 2026-05-08)
- ✅ **v5.1 Kapsamlı Bug Fix & Kalite İyileştirme** — Phases 40–42 (completed 2026-05-08)
- 🚧 **v6.0 Karar Güvenliği & Sistem Olgunlaşması** — Phases 43–47 (aktif)

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

<details>
<summary>✅ v5.0 LLM Entegrasyonlu Yatırım Asistanı (Phases 34–39) — COMPLETED 2026-05-08</summary>

- [x] **Phase 34: Frontend Tasarım Düzeltmeleri** — 6 tasarım tutarsızlığı giderildi (completed 2026-05-08)
- [x] **Phase 35: Gemini LLM Altyapısı** — Backend Gemini 2.0 Flash servis katmanı; quota fallback; async generate (completed 2026-05-08)
- [x] **Phase 36: Hisse Detay + AI Analizi** — `/stocks/[symbol]` sayfası tamamen dolduruldu: fiyat grafiği, temel + teknik metrik kartları, on-demand Gemini analizi (completed 2026-05-08)
- [x] **Phase 37: Haberler + Günlük AI Özeti** — `/intelligence` sayfası KAP + basın verisiyle dolduruldu; günlük Gemini piyasa özeti kartı (completed 2026-05-08)
- [x] **Phase 38: Portföy + Takip Listesi** — `/portfolio` alım-satım girişi, gerçek P&L hesaplama, BIST100 karşılaştırması (completed 2026-05-08)
- [x] **Phase 39: Model Portföy AI Kararları** — `/model-portfolio` Gemini haftalık özerk kararlar + Türkçe gerekçe + karar geçmişi (completed 2026-05-08)

</details>

### v5.1 Kapsamlı Bug Fix & Kalite İyileştirme (Phases 40–42) — AKTİF

**Milestone Hedefi:** v5.0'da gönderilen tüm özellikleri olgunlaştır; görsel hatalar, veri doğruluğu, eksik fonksiyonlar ve AI kalitesi olmak üzere 4 alanda kapsamlı düzeltme yap.

- [ ] **Phase 40: UI/UX Kapsamlı Görsel İyileştirme** — Tüm 7 sayfada sistematik görsel geçiş, mobile responsive düzeltmeleri, empty state standardizasyonu
- [ ] **Phase 41: Veri Doğruluğu & Eksik Fonksiyonlar** — Hesaplama hatalarını düzelt, null güvenliği ekle, watchlist/portföy eksik fonksiyonlarını tamamla
- [ ] **Phase 42: AI Kalite & Sistem Güvenilirliği** — Tüm AI prompt'larını derinleştir, hata yönetimini standardize et, sistem kararlılığını sağla

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
**Plans**: 1 plan

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
**Plans**: 1 plan

Plans:
- [x] 35-01: GeminiService sınıfı — SDK entegrasyonu, async generate, quota fallback, unit testler

### Phase 36: Hisse Detay Sayfası + AI Analizi
**Goal**: Şu an "Hisse bulunamadı." mesajı veren `/stocks/[symbol]` sayfası gerçek veriyle tamamen doldurulur; Gemini on-demand Türkçe analiz eklenir.
**Depends on**: Phase 35
**Requirements**: STCK-01, STCK-02, STCK-03, STCK-04, LLM-02, DISC-03
**Success Criteria** (what must be TRUE):
  1. `/stocks/AKBNK` gibi bir URL'de hisse adı, fiyat, günlük değişim ve fiyat grafiği (7g / 1ay / 3ay / 1y tab) görünür
  2. Temel metrikler (F/K, PD/DD, net kar, bilanço büyümesi) ve teknik göstergeler (RSI, MACD, hareketli ortalamalar) her birinin yanında Türkçe tooltip açıklamasıyla görünür
  3. Teknik skorun altında "güçlü / nötr / zayıf" gibi Türkçe sinyal etiketleri bulunur
  4. "Analiz Et" butonuna basıldığında Gemini o hisseye özel Türkçe analiz üretir; aynı oturumda tekrar istek gönderilmez; Gemini yanıt verene kadar loading gösterilir
  5. `/stocks` listesindeki her hisse ismine tıklandığında ilgili detay sayfasına gidilir (DISC-03)
**Plans**: 1 plan

Plans:
- [x] 36-01-PLAN.md — Backend POST analyze endpoint + frontend Analiz Et butonu, tooltiplar (STCK-02, STCK-04, LLM-02)

### Phase 37: Haberler + Günlük AI Özeti
**Goal**: Mevcut `/intelligence` sayfası (sidebar: "Haberler") KAP + basın verisiyle doldurulur; dashboard'a ve haberler sayfasına her sabah otomatik Gemini piyasa özeti kartı eklenir.
**Depends on**: Phase 35
**Requirements**: NEWS-01, LLM-03, STCK-05, STCK-06
**Success Criteria** (what must be TRUE):
  1. `/intelligence` sayfasında KAP açıklamaları ve basın haberlerinin tarih sıralı birleşik akışı görünür; KAP/Piyasa/Makro/Resmi filtreleri çalışır
  2. Yeni haberler sayfanın başına eklenir; sayfalama veya sonsuz kaydırma ile eski haberler de görülebilir
  3. Dashboard'ın en üstünde (BIST100 kartı altında) o güne ait Gemini piyasa özeti kartı görünür; kart tarih + özet içerir
  4. Aynı özet `/intelligence` sayfasının en üstünde de görünür
  5. APScheduler her sabah 09:00'da yeni özeti üretir; Gemini yanıt vermezse kart gizlenir, sayfa bozulmaz
**Plans**: 1 plan

Plans:
- [x] 37-01-PLAN.md — Günlük Gemini piyasa özeti: /intelligence/daily-summary endpoint, APScheduler 09:05 cache reset, dashboard + haberler banner (LLM-03)

### Phase 38: Portföy + Takip Listesi
**Goal**: Mevcut `/portfolio` sayfasının tam tasarımı çalışır hale getirilir: alım-satım girişi, gerçek P&L hesaplama, BIST100 karşılaştırması. Mevcut `/watchlist` sayfası hisse ekleme/çıkarma ve canlı fiyatla çalışır.
**Depends on**: Phase 29
**Requirements**: PORT-01, PORT-02, PORT-03, PORT-04, PORT-05
**Success Criteria** (what must be TRUE):
  1. "+Yeni Pozisyon" butonuyla hisse, lot, fiyat, tarih girilebilir; kayıt anında portföy listesine yansır
  2. Pozisyon kapatılınca kapanış fiyatı girilerek gerçekleşen kâr/zarar (TL + %) hesaplanıp görünür
  3. Açık pozisyonlar güncel fiyatla hesaplanmış TL ve % kâr/zarar gösterir; risk özeti (aktif pozisyon, stop yakın, hedef yakın) doğru hesaplanır
  4. Portföy değer grafiği BIST100 ile aynı başlangıç noktasından karşılaştırılır
  5. `/watchlist` sayfasında hisse yıldızlanabilir/çıkarılabilir; takip listesi canlı fiyat + günlük değişim gösterir
**Plans**: 1 plan

Plans:
- [x] 38-01-PLAN.md — PORT-02 pozisyon kapatma: DB migration, PATCH endpoint, frontend Kapat butonu + Geçmiş Pozisyonlar tablosu

### Phase 39: Model Portföy AI Kararları
**Goal**: Mevcut `/model-portfolio` sayfası Gemini tarafından haftalık özerk olarak yönetilen gerçek bir model portföyle doldurulur; her karar Türkçe gerekçesiyle tarihli olarak kaydedilir.
**Depends on**: Phase 35, Phase 38
**Requirements**: MODEL-01, MODEL-02, MODEL-03, MODEL-04, LLM-04
**Success Criteria** (what must be TRUE):
  1. "Haftalık Model Portföy" bölümünde mevcut modelin pozisyonları (hisse, ağırlık, giriş fiyatı, P&L) görünür
  2. APScheduler her Pazartesi sabahı BIST100 evreni içinde model portföyü günceller; insan müdahalesi olmaz
  3. Her alım/satım kararı Gemini'nin Türkçe gerekçesiyle birlikte tarih damgalı olarak kaydedilir ve sayfada "Karar Geçmişi" bölümünde görünür
  4. Kullanıcı kendi portföy performansını (Phase 38) model portföyüyle grafik üzerinde karşılaştırabilir
  5. Gemini quota aşılırsa kararlar üretilemez ama mevcut pozisyonlar ve geçmiş görünmeye devam eder
**Plans**: 1 plan

Plans:
- [x] 39-01-PLAN.md — Gemini haftalık özet entegrasyonu + model portföy geçmişi + kullanıcı karşılaştırma kartı (MODEL-02, MODEL-03, MODEL-04, LLM-04)

### Phase 40: UI/UX Kapsamlı Görsel İyileştirme
**Goal**: Tüm 7 sayfada piksel düzeyinde görsel geçiş tamamlanır; mobile responsive düzeltmeleri yapılır ve boş durumlar (empty states) standardize edilir.
**Depends on**: Phase 39
**Requirements**: UI-01, UI-02, UI-03, UI-04, UI-05
**Success Criteria** (what must be TRUE):
  1. Tüm 7 sayfada (dashboard, stocks, stock-detail, intelligence, portfolio, watchlist, model-portfolio) layout, spacing ve renk tutarsızlıkları giderilir; bir sayfadan diğerine geçişte görsel bütünlük bozulmaz
  2. 375px (mobil) ve 768px (tablet) kırılım noktalarında tüm sayfalarda içerik taşmaz, butonlar tıklanabilir kalır, metinler okunabilir görünür
  3. Her sayfada veri yokken tutarlı Türkçe boş durum mesajı ve ilgili aksiyon butonu görünür; farklı sayfalarda birbiriyle çelişen empty state tasarımları kalmaz
  4. Veri yüklenirken skeleton ekran gösterilir; API hatası durumunda tüm sayfalarda aynı stil hata mesajı görünür; kullanıcı boş beyaz ekranla karşılaşmaz
  5. Hisse detay sayfasında hero bölümü ve temel metrik kartları (fundGrid) mobil ve masaüstünde düzgün hizalanır; kartlar içeriği kesmeden görünür
**Plans**: TBD

### Phase 41: Veri Doğruluğu & Eksik Fonksiyonlar
**Goal**: Portföy K/Z hesaplama hataları düzeltilir, tüm sayfalarda null/undefined güvenliği sağlanır ve yarım kalan watchlist ile portföy fonksiyonları tamamlanır.
**Depends on**: Phase 40
**Requirements**: DATA-01, DATA-02, DATA-03, FEAT-01, FEAT-02, FEAT-03
**Success Criteria** (what must be TRUE):
  1. Portföy sayfasında ve dashboard portföy özetinde kapalı pozisyonların kâr/zarar değeri doğru hesaplanır; negatif P&L artı, artı P&L negatif görünmez
  2. Tüm sayfalarda API'den null veya undefined gelen değerler NaN veya JavaScript hatası fırlatmaz; kullanıcı "—" veya "Veri yok" gibi anlamlı bir placeholder görür
  3. Hisse detay sayfasında F/K, PD/DD gibi teknik/temel metrikler eksik geldiğinde boş kutu yerine görsel placeholder (çizgi veya "Veri Yok" etiketi) gösterilir
  4. Hisse detay sayfasındaki "İzlemeye Ekle/Çıkar" butonu çalışır; işlem sonucu watchlist sayfasına localStorage üzerinden anında yansır; sayfa yenilenmeden durum güncellenir
  5. Portföy pozisyon ekleme formu geçersiz girdi (sıfır lot, negatif fiyat, boş hisse) için client-side validasyon mesajı gösterir; başarılı kayıt sonrası liste otomatik yenilenir
  6. BIST100 vs portföy karşılaştırma grafiği, portföy verisi mevcut olduğunda bozulmadan render edilir; grafik aynı zaman ekseninde her iki seriyi gösterir
**Plans**: TBD

### Phase 42: AI Kalite & Sistem Güvenilirliği
**Goal**: Tüm AI prompt'ları derinleştirilir; her AI endpoint'de standart hata yönetimi uygulanır; sistem kesintisiz ve güvenilir çalışır.
**Depends on**: Phase 41
**Requirements**: AI-01, AI-02, AI-03, AI-04
**Success Criteria** (what must be TRUE):
  1. Hisse analizi Gemini çıktısı valuasyon yorumu (ucuz/pahalı mı?), sektör bağlamı ve net risk/fırsat dengesi içerir; genel bir özet yerine o hisseye özgü somut yorum sunar
  2. Günlük piyasa özeti kartı döviz (USD/TRY), faiz ve küresel piyasa hareketlerini makro bağlamda ele alır; cache doğru çalışır, her sabah 09:05'te yeni özet gelir ve eski kart kaybolmaz
  3. Model portföy haftalık karar döngüsünde Gemini her alım/satım kararı için Türkçe gerekçe yazar ve bu gerekçe veritabanına doğru kaydedilir; geçmiş kararlar sayfada listelenir
  4. Tüm AI endpoint'lerinde (hisse analizi, günlük özet, model portföy kararı) hata durumunda kullanıcı dostu Türkçe fallback mesajı gösterilir; HTTP 500 kullanıcıya hiçbir zaman ham olarak iletilmez
**Plans**: TBD

---

## v6.0 Phases

### Phase 43: Karar Dili Güvenliği & Skor Açıklanabilirliği
**Goal**: "GÜÇLÜ AL/SAT" gibi direktif etiketler direktif olmayan güvenli dile çevrilir; hisse detay sayfasında skor bileşen dökümü ve veri bütünlüğü göstergesi eklenir.
**Depends on**: Phase 42 (v5.1 tamamlandı)
**Requirements**: KARAR-01, KARAR-02, KARAR-03, KARAR-04, SKOR-01, SKOR-02, SKOR-03
**Success Criteria** (what must be TRUE):
  1. Hisse listesinde ve hisse detay sayfasında "GÜÇLÜ AL" / "AL" / "TUT" / "SAT" / "GÜÇLÜ SAT" etiketleri artık görünmez; yerine "Yüksek Öncelikli İzleme" / "Pozitif Görünüm" / "Nötr İzleme" / "Zayıflayan Görünüm" / "Riskli Görünüm" etiketleri gösterilir
  2. Etiketin üzerine hover edildiğinde veya bilgi ikonuna tıklandığında "Bu karar destek notudur — nihai karar kullanıcıya aittir" içerikli tooltip/not görünür
  3. Hisse detay sayfasında veri bütünlüğü göstergesi bulunur: "3/3 bileşen mevcut" veya "2/3 — temel veri eksik" şeklinde
  4. Temel verisi eksik veya volatilitesi yüksek hisselerde görsel uyarı işareti (sarı ikon veya metin) görünür
  5. Hisse detay sayfasında skor bileşen dökümü gösterilir: Temel %45 → 29.2 puan, Teknik %40 → 28.8 puan, Sentiment %15 → 8.1 puan formatında; veriler backend score-breakdown API'den gelir
  6. Bileşen eksikse (ör. temel veri yok) "Ağırlık yeniden dağıtıldı — temel veri mevcut değil" uyarısı gösterilir
**Plans**: 2 plans

Plans:
- [x] 43-01-PLAN.md — Guvenli etiket mapping + tooltip (KARAR-01, KARAR-04) — stocks, stock detail, model-portfolio, dashboard
- [ ] 43-02-PLAN.md — Skor doküm bölümü + veri bütünlüğü göstergesi (KARAR-02, KARAR-03, SKOR-01, SKOR-02, SKOR-03)

### Phase 44: Backtest & Sinyal Performans Dashboard
**Goal**: Mevcut sinyal snapshot + outcome evaluation altyapısı kullanıcıya görünür hale getirilir; hit ratio ve getiri istatistikleri ile birlikte sinyal performans tablosu sunulur.
**Depends on**: Phase 43
**Requirements**: BACKTEST-01, BACKTEST-02, BACKTEST-03, BACKTEST-04
**Success Criteria** (what must be TRUE):
  1. Portfolio veya Intelligence sayfasında "Sinyal Performansı" bölümü bulunur; tablo: sinyal tarihi, hisse sembolü, etiket, 1 haftalık getiri (%), 1 aylık getiri (%), BIST100'e göre fark, başarılı mı sütunlarını içerir
  2. Dönem filtresi çalışır: son 1 ay / 3 ay / 6 ay seçimlerinde tablo ilgili sinyalleri gösterir
  3. Etiket filtresi çalışır: "Pozitif Görünüm", "Yüksek Öncelikli İzleme" gibi seçimle tablo filtrelenir
  4. Özet satırı gösterilir: "toplam X sinyal, %Y tuttu, ortalama 1 haftalık getiri: +Z%"
  5. Veri yoksa "Henüz değerlendirilebilir sinyal yok — sistem sinyaller ürettikçe burada görünecek" mesajı gösterilir
  6. Backend'den sinyal verisi alınırken hata oluşursa kullanıcı dostu Türkçe mesaj gösterilir
**Plans**: TBD

### Phase 45: Veri Tazeliği & Sistem Sağlığı
**Goal**: Tüm sayfalarda verinin ne zaman güncellendiği gösterilir; stale data görsel uyarısı eklenir; AI analizine veri tarihi notu eklenir.
**Depends on**: Phase 43
**Requirements**: VERI-01, VERI-02, VERI-03, VERI-04
**Success Criteria** (what must be TRUE):
  1. Hisse listesindeki her hisse satırında (veya tablonun üstünde) son fiyat güncelleme zamanı gösterilir: "Son güncelleme: 14:32" veya "Son güncelleme: 3 saat önce" formatında
  2. Hisse detay sayfasında fundamental veri dönemi etiketi görünür: "Temel Veriler — 2024-Q3 dönemi" gibi
  3. Son güncelleme 8 saatten eski olan hisselerde sarı renkli veya "⚠ Eski veri" metniyle görsel uyarı gösterilir
  4. Hisse AI analiz sonucunun altında "Bu analiz [tarih] verilerine dayanmaktadır" notu yer alır
  5. Uyarılar kullanıcı deneyimini bozmadan sade ve okunabilir şekilde gösterilir (tabloya dikey alan eklemeden)
**Plans**: TBD

### Phase 46: Portföy Risk Yönetimi
**Goal**: Portföy sayfasına sektör dağılımı görselleştirmesi ve yoğunlaşma uyarısı eklenir; özet karta risk bilgileri entegre edilir.
**Depends on**: Phase 44
**Requirements**: RISK-01, RISK-02, RISK-03, RISK-04
**Success Criteria** (what must be TRUE):
  1. Portföy sayfasında sektör dağılımı bölümü yer alır: her sektörün adı ve portföydeki ağırlığı (%) listelenir veya yatay bar grafik ile gösterilir
  2. Herhangi bir sektörün ağırlığı %35'i geçtiğinde görsel uyarı (turuncu/sarı renk veya ikon) gösterilir: "Bankacılık sektöründe yoğunlaşma: %42 ⚠"
  3. Herhangi bir hissenin portföy ağırlığı %20'yi geçtiğinde görsel uyarı gösterilir: "AKBNK tek hisse ağırlığı: %24 ⚠"
  4. Portföy özet kartına "Açık pozisyon: X hisse" ve "En büyük 3 sektör: Bankacılık %42, Enerji %18, Sanayi %15" bilgisi eklenir
  5. Uyarılar pozisyon listesinin üstünde veya ayrı bir risk özeti bölümünde gösterilir; K/Z tablosuna müdahale etmez
**Plans**: TBD

### Phase 47: İşlem Disiplini & Günlüğü
**Goal**: Pozisyon açma formuna disiplin alanları eklenir; pozisyon kapatmada çıkış nedeni zorunlu hale gelir; kapalı pozisyon istatistikleri gösterilir.
**Depends on**: Phase 46
**Requirements**: GUNLUK-01, GUNLUK-02, GUNLUK-03, GUNLUK-04
**Success Criteria** (what must be TRUE):
  1. Pozisyon ekleme formunda "Kararı bozan koşul" metin alanı bulunur (zorunlu değil, placeholder açıklayıcı: "Ör. MACD negatif geçerse veya 90 TL altına sararsa")
  2. Pozisyon kapatma diyaloğunda çıkış nedeni seçimi zorunludur: Stop Tetiklendi / Hedefe Ulaştı / Senaryo Bozuldu / Diğer
  3. Kapalı pozisyonlar listesinde her pozisyon için giriş gerekçesi (varsa) ve çıkış nedeni görünür
  4. Portfolio sayfasında kapalı pozisyon istatistik özeti gösterilir: toplam kapatılan pozisyon sayısı, ortalama K/Z (%), planlı çıkış oranı (stop+hedef / toplam)
  5. "Diğer" seçildiğinde kısa açıklama metin alanı açılır
  6. Backend'e exit_reason ve invalidation_condition alanları eklenir ve kaydedilir
**Plans**: TBD

## Progress Table

**Execution Order:**
v5.0 phases: 34 → 35 → 36 → 37 → 38 → 39 (complete)
v5.1 phases: 40 → 41 → 42 (complete)
v6.0 phases: 43 → 44+45 (parallel) → 46 → 47

| Phase | Milestone | Sayfalar | Plans | Status | Tamamlandı |
|-------|-----------|----------|-------|--------|-----------|
| 22. Async Infrastructure | v3.1 | — | 2/2 | ✅ Complete | 2026-04-29 |
| 23. Security Hardening | v3.1 | — | 1/1 | ✅ Complete | 2026-04-28 |
| 24. Data Reliability | v3.1 | — | 1/1 | ✅ Complete | 2026-04-28 |
| 25. Business Logic Correctness | v3.1 | — | 1/1 | ✅ Complete | 2026-04-28 |
| 26. Frontend Quality | v3.1 | — | 1/1 | ✅ Complete | 2026-04-28 |
| 27. Infrastructure Upgrade | v3.1 | — | 1/1 | ✅ Complete | 2026-04-29 |
| 28. Veri Altyapısı | v4.0 | — | 3/3 | ✅ Complete | 2026-05-05 |
| 29. Dashboard | v4.0 | `/` | 2/2 | ✅ Complete | 2026-05-07 |
| 34. Frontend Tasarım Düzeltmeleri | v5.0 | tüm | 2/2 | ✅ Complete | 2026-05-08 |
| 35. Gemini LLM Altyapısı | v5.0 | backend | 1/1 | ✅ Complete | 2026-05-08 |
| 36. Hisse Detay + AI Analizi | v5.0 | `/stocks/[symbol]` | 1/1 | ✅ Complete | 2026-05-08 |
| 37. Haberler + Günlük AI Özeti | v5.0 | `/intelligence` + `/` | 1/1 | ✅ Complete | 2026-05-08 |
| 38. Portföy + Takip Listesi | v5.0 | `/portfolio` + `/watchlist` | 1/1 | ✅ Complete | 2026-05-08 |
| 39. Model Portföy AI Kararları | v5.0 | `/model-portfolio` | 1/1 | ✅ Complete | 2026-05-08 |
| 40. UI/UX Kapsamlı Görsel İyileştirme | v5.1 | tüm 7 sayfa | 1/1 | ✅ Complete | 2026-05-08 |
| 41. Veri Doğruluğu & Eksik Fonksiyonlar | v5.1 | `/portfolio` + `/stocks/[symbol]` | 1/1 | ✅ Complete | 2026-05-08 |
| 42. AI Kalite & Sistem Güvenilirliği | v5.1 | backend + AI endpoint'ler | 1/1 | ✅ Complete | 2026-05-08 |
| 43. Karar Dili & Skor Açıklanabilirliği | v6.0 | `/stocks` + `/stocks/[symbol]` | 0/? | ⬜ Not started | — |
| 44. Backtest & Sinyal Dashboard | v6.0 | `/intelligence` veya `/portfolio` | 0/? | ⬜ Not started | — |
| 45. Veri Tazeliği & Sistem Sağlığı | v6.0 | `/stocks` + `/stocks/[symbol]` + AI | 0/? | ⬜ Not started | — |
| 46. Portföy Risk Yönetimi | v6.0 | `/portfolio` | 0/? | ⬜ Not started | — |
| 47. İşlem Disiplini & Günlüğü | v6.0 | `/portfolio` + backend | 0/? | ⬜ Not started | — |

## Kuzey Yıldızı

Stalize, BIST100 odaklı ama BIST'i etkileyen yerel ve küresel tüm önemli akışları izleyebilen, tamamen gerçek veriye dayalı bir analiz terminalidir. Amaç günlük trade terminali değil; özellikle 3-12 ay ufkunda daha güçlü hisse seçimi ve portföy yönetimi yaptıran bir karar sistemi kurmak.

**Temel ilkeler:**
1. Mock yok, simülasyon yok, sentetik haber yok.
2. KAP şirket verisinde birinci kaynak.
3. Kaynak önceliği ülkeye göre değil, BIST etkisine göre.
4. Dokunulan her fazda UI tutarsızlığı aynı turda düzeltilir.
5. Veri gelmiyorsa sistem boş döner; yanlış tahmin üretmez.
