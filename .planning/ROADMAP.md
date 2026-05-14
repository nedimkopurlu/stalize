# Roadmap: Stalize Gerçek Veri Finansal Analiz Sistemi

## Milestones

- ✅ **v2.0 Gerçek Veri Çekirdeği** — Phases 01–16 (shipped 2026-04-27)
- ✅ **v3.0 Tüm Borsa + Kullanılabilir Platform** — Phases 17–21 (shipped 2026-04-28)
- ✅ **v3.1 Audit Düzeltmeleri** — Phases 22–27 (shipped 2026-04-29)
- ✅ **v4.0 Kişisel Yatırım Asistanı** — Phases 28–29 (completed); Phases 30–33 absorbed into v5.0
- ✅ **v5.0 LLM Entegrasyonlu Yatırım Asistanı** — Phases 34–39 (completed 2026-05-08)
- ✅ **v5.1 Kapsamlı Bug Fix & Kalite İyileştirme** — Phases 40–42 (completed 2026-05-08)
- ✅ **v6.0 Karar Güvenliği & Sistem Olgunlaşması** — Phases 43–47 (shipped 2026-05-14)
- 🔄 **v7.0 Analiz Kalitesi & Sistem Bütünlüğü** — Phases 48–55 (in progress)

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

<details>
<summary>✅ v5.1 Kapsamlı Bug Fix & Kalite İyileştirme (Phases 40–42) — SHIPPED 2026-05-08</summary>

- [x] **Phase 40: UI/UX Kapsamlı Görsel İyileştirme** — Tüm 7 sayfada sistematik görsel geçiş, mobile responsive düzeltmeleri, empty state standardizasyonu
- [x] **Phase 41: Veri Doğruluğu & Eksik Fonksiyonlar** — Hesaplama hatalarını düzelt, null güvenliği ekle, watchlist/portföy eksik fonksiyonlarını tamamla
- [x] **Phase 42: AI Kalite & Sistem Güvenilirliği** — Tüm AI prompt'larını derinleştir, hata yönetimini standardize et, sistem kararlılığını sağla

Full details: `.planning/milestones/v6.0-ROADMAP.md`

</details>

### v7.0 Analiz Kalitesi & Sistem Bütünlüğü (Phases 48–55) — AKTİF

**Milestone Hedefi:** BIST audit bulgularındaki tüm eksiklikleri kapatmak — Türkçe NLP, veri kalitesi, sektör bazlı scoring, market regime, portföy derinliği, backtest kalitesi.

- [ ] **Phase 48: Veri Kalitesi Temeli** — yfinance USD→TRY sanity check, data quality score, safeLabel utility
- [ ] **Phase 49: Veri Zenginleştirme** — Tavan/taban tespiti, likidite skoru, KAP duyuru sınıflandırması
- [ ] **Phase 50: Market Regime Engine** — ADX+EMA200+ATR kural tabanlı rejim tespiti, USD-adjusted XU100.IS
- [ ] **Phase 51: Sektör Bazlı Skorlama** — Banka P/TBV+ROE, GYO P/B proxy, Holding NAV yaklaşımı
- [ ] **Phase 52: Portföy Analizi** — Portföy beta, korelasyon matrisi, pozisyon büyüklüğü rehberi
- [ ] **Phase 53: Türkçe NLP & Sentiment** — VADER kaldır, GPT-4o-mini KAP sentiment, Türkçe RSS kural seti
- [ ] **Phase 54: Backtest Kalitesi** — Likidite bazlı slipaj, %0.1 komisyon, rejim bazlı backtest filtreleme
- [ ] **Phase 55: UI — Hisse Detay & Ön-işlem Checklist** — Detay sayfa hiyerarşisi, 7 maddelik ön-işlem checklist

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

<details>
<summary>✅ v6.0 Karar Güvenliği & Sistem Olgunlaşması (Phases 43–47) — SHIPPED 2026-05-14</summary>

- [x] Phase 43: Karar Dili Güvenliği & Skor Açıklanabilirliği (2 plans) — safeLabel, skor dökümü, volatilite uyarısı
- [x] Phase 44: Backtest & Sinyal Performans Dashboard (2 plans) — /backtest sayfası, KPI, filtreler, 7 sütun
- [x] Phase 45: Veri Tazeliği & Sistem Sağlığı (2 plans) — stale banner, updated_at, AI tarih notu, period badge
- [x] Phase 46: Portföy Risk Yönetimi (2 plans) — sektör bar chart, yoğunlaşma uyarıları, risk özet kartı
- [x] Phase 47: İşlem Disiplini & Günlüğü (3 plans) — exit_reason, invalidation_condition, kapalı poz. stats

Full details: `.planning/milestones/v6.0-ROADMAP.md`

</details>

---

### Phase 48: Veri Kalitesi Temeli
**Goal**: Kullanıcı, yfinance'ten gelen BIST fundamental verilerinin güvenilirliğini anlık olarak görebilir; şüpheli USD→TRY dönüşüm hataları tespit edilip işaretlenir.
**Depends on**: Phase 47
**Requirements**: VKL-01, VKL-02, TECH-01
**Success Criteria** (what must be TRUE):
  1. Kullanıcı, hisse listesinde ve hisse detay sayfasında her hisse için 0-100 arasında data quality score görür; düşük skorlu hisseler "Düşük Veri Güveni" uyarısıyla işaretlenir.
  2. Yfinance'ten gelen fundamental değer USD cinsinden görünüyorsa (örn. çok küçük F/K, beklenmedik oran) sistem otomatik "düşük güven" bayrağı koyar; kullanıcı bu veriye dayanarak karar almaya yönlendirilmez.
  3. `safeLabel()` fonksiyonu `StockHelpers.tsx`'te tek kaynak olarak tanımlanır; 5 sayfadaki inline kopyalar bu tek kaynaktan import edilir; kod tabanında duplikasyon kalmaz.
  4. `stocks.data_quality_score` sütunu Alembic migration ile DB'ye eklenir; mevcut kayıtlar `null` ile başlar, ilk hesaplama sonrası güncellenir.
**Plans**: TBD

### Phase 49: Veri Zenginleştirme
**Goal**: Kullanıcı, tavan/taban durumundaki hisseleri anında fark eder ve ince piyasalı hisselerde likidite uyarısıyla karşılaşır; KAP duyuruları kategori badge'iyle gösterilir.
**Depends on**: Phase 48
**Requirements**: VKL-03, VKL-04, KAP-01, KAP-02
**Success Criteria** (what must be TRUE):
  1. Hisse detay sayfasında fiyat kutusunda tavan/taban durumu renkli badge ile gösterilir (tavan: kırmızı, taban: yeşil); OHLCV verisi yoksa badge gizlenir.
  2. Kullanıcı, Amihud illiquidity ratio tabanlı 3 kademeli likidite sınıflandırmasını (Yüksek/Orta/Düşük Likidite) hisse listesinde ve detay sayfasında görür; "Düşük Likidite" hisseler için uyarı mesajı gösterilir.
  3. KAP duyuruları otomatik olarak tip koduna göre kategorize edilir (Finansal Sonuçlar, Temettü, Sermaye Artırımı, İçeriden Öğrenme, Düzenleyici); sınıflandırılamayan duyurular "Diğer" kategorisine düşer.
  4. Hisse detay sayfasındaki KAP listesinde her duyurunun yanında kategori badge'i görünür; Temettü ve Sermaye Artırımı kategorileri vurgulanır.
  5. `price_history.is_tavan`, `price_history.is_taban` ve `stocks.liquidity_score`, `stocks.liquidity_label` sütunları Alembic migration ile eklenir.
**Plans**: TBD

### Phase 50: Market Regime Engine
**Goal**: Sistem, BIST100 piyasa rejimini otomatik olarak tespit eder ve bu bilgi hem dashboard'da hem hisse detay sayfasında görünür hale gelir.
**Depends on**: Phase 48
**Requirements**: REJ-01, REJ-02
**Success Criteria** (what must be TRUE):
  1. Sistem her 60 dakikada bir BIST100 için piyasa rejimini hesaplar (Boğa / Ayı / Yatay / Volatil); ADX, EMA200 ve ATR değerleri kural tabanlı algoritmaya girdi olarak kullanılır; USD-adjusted XU100.IS kullanılır.
  2. Dashboard'da mevcut piyasa rejimi badge olarak görünür (renk + Türkçe etiket); kullanıcı sayfayı yenilemeden son rejimi görür.
  3. Hisse detay sayfasında da aynı regime badge gösterilir; hisse skoru yorumlanırken rejim bağlamı sunulur.
  4. `market_regimes` tablosu DB'ye eklenir; APScheduler 60 dakikada bir regime hesaplama jobunu çalıştırır.
**Plans**: TBD

### Phase 51: Sektör Bazlı Skorlama
**Goal**: Bankacılık, GYO ve Holding hisseleri için sektöre özgü skorlama mantığı devreye girer; yanıltıcı standart metrikler bu sektörlerde uygulanmaz.
**Depends on**: Phase 48
**Requirements**: SEK-01, SEK-02, SEK-03
**Success Criteria** (what must be TRUE):
  1. Bankacılık hisseleri için skor hesaplamasında F/DD (P/TBV) ve ROE ağırlıklı sektör skoru kullanılır; standart PE/PB bu hisseler için skoru etkilemez; hisse detay sayfasında "Banka Sektörü Skoru" açıklaması görünür.
  2. GYO hisseleri için P/B değeri NAV proxy olarak kullanılır ve skor buna göre hesaplanır; detay sayfasında "Gerçek NAD verisi mevcut değil" uyarı notu gösterilir.
  3. Holding hisseleri için halka açık bağlı ortaklıkların piyasa değerleri toplanarak yaklaşık NAV iskontosu hesaplanır ve skora yansıtılır; bu hesaplama yaklaşık olduğuna dair not gösterilir.
  4. yfinance'ten gelen sektör string değerleri normalizasyon haritasıyla standartlaştırılır; bilinmeyen sektörler genel skorlamaya düşer.
**Plans**: TBD

### Phase 52: Portföy Analizi
**Goal**: Kullanıcı, portföyünün piyasaya karşı betasını, pozisyonlar arası korelasyonu ve volatilite bazlı pozisyon büyüklüğü önerisini portföy sayfasında görür.
**Depends on**: Phase 48
**Requirements**: PORT-01, PORT-02, PORT-03
**Success Criteria** (what must be TRUE):
  1. Portföy sayfasında portföy betası görünür (252 günlük pencere, 0-3 aralığına kırpılmış, BIST100 benchmark); beta 1'den büyükse "Piyasadan Daha Volatil" uyarısı gösterilir.
  2. Portföydeki pozisyonlar arası korelasyon matrisi portföy sayfasında görünür; yüksek korelasyonlu çiftler (>0.7) vurgulanır.
  3. Kullanıcı, potansiyel bir pozisyon için hisse detay sayfasında volatilite bazlı pozisyon büyüklüğü önerisi görür (%1-2 risk kuralı, ATR×2 stop mesafesi temelinde).
  4. Portföy beta ve korelasyon hesaplamaları için yeni API endpoint'leri oluşturulur; frontend bu endpoint'leri çağırır.
**Plans**: TBD

### Phase 53: Türkçe NLP & Sentiment
**Goal**: VADER kaldırılır; KAP duyuruları OpenAI GPT-4o-mini ile Türkçe sentiment analizine tabi tutulur; RSS haber akışları Türkçe kural setiyle sınıflandırılır.
**Depends on**: Phase 49
**Requirements**: NLP-01, NLP-02
**Success Criteria** (what must be TRUE):
  1. `vaderSentiment` paketi `requirements.txt`'ten kaldırılır; codebase'de VADER import veya kullanımı kalmaz.
  2. KAP duyuruları APScheduler job'u aracılığıyla OpenAI GPT-4o-mini'ye gönderilir; batch sentiment analizi sonuçları DB'ye yazılır; sentiment skoru hisse detay sayfasında KAP kartında görünür.
  3. RSS haber akışları Türkçe pozitif/negatif/nötr anahtar kelime kurallarıyla sınıflandırılır; sınıflandırma sonucu haber listesinde renk kodu ile gösterilir.
  4. APScheduler KAP sentiment job'u günlük çalışır; OpenAI API erişilemezse mevcut sentiment değerleri korunur, sistem çökmez.
**Plans**: TBD

### Phase 54: Backtest Kalitesi
**Goal**: Backtest simülasyonu gerçekçi maliyet modeliyle çalışır; sonuçlar likidite kademesi ve piyasa rejimine göre ayrılmış olarak sunulur.
**Depends on**: Phase 50, Phase 52
**Requirements**: BACK-01, BACK-02, REJ-03
**Success Criteria** (what must be TRUE):
  1. Backtest simülasyonu BIST30 hisseleri için 10bps, sıra 30-70 için 20bps, sıra 70-100 için 40bps slipaj modeli uygular; ayrıca %0.1 işlem komisyonu hesaba katılır; sonuçlar mevcut ham sonuçlardan farklılaşır.
  2. `/backtest` sayfasında sonuçlar rejim bazında filtrelenebilir (Boğa / Ayı / Yatay / Volatil dönem performans karşılaştırması); her rejim için ayrı metrikler gösterilir.
  3. Kullanıcı, farklı piyasa koşullarında sinyallerin nasıl performans gösterdiğini karşılaştırmalı tabloda görür; "Boğa piyasasında %X başarı, Ayı piyasasında %Y başarı" gibi somut metrikler sunulur.
**Plans**: TBD

### Phase 55: UI — Hisse Detay & Ön-işlem Checklist
**Goal**: Hisse detay sayfası hiyerarşik bölüm yapısına kavuşur; kullanıcı pozisyon açmadan önce otomatik doldurulmuş 7 maddelik ön-işlem checklist görür.
**Depends on**: Phase 49, Phase 50, Phase 52, Phase 54
**Requirements**: UI-01, UI-02
**Success Criteria** (what must be TRUE):
  1. Hisse detay sayfası hiyerarşik bölüm düzenine sahiptir: Hero (fiyat, badge'ler) → Skor Özeti → Teknik → Temel → Haberler → Regime → İlgili Hisseler; bölümler mantıksal sırayla gösterilir.
  2. "Pozisyon Aç" bölümünde 7 maddelik ön-işlem checklist otomatik olarak doldurulur: piyasa rejimi, likidite durumu, toplam skor, diğer pozisyonlarla korelasyon, tavan/taban durumu, önerilen pozisyon büyüklüğü, çıkış planı; her madde geçti/başarısız/uyarı durumunu gösterir.
  3. Checklist'teki tüm 7 madde mevcut hesaplama verilerinden otomatik beslenir; kullanıcı manuel giriş yapmaz.
  4. Checklist sayfası render hatası durumunda bölüm gizlenir; sayfa çökmez.
**Plans**: TBD

---

## Progress Table

**Execution Order:**
v5.0 phases: 34 → 35 → 36 → 37 → 38 → 39 (complete)
v5.1 phases: 40 → 41 → 42 (complete)
v6.0 phases: 43 → 44+45 (parallel) → 46 → 47
v7.0 phases: 48 → 49+50+51+52 (parallel after 48) → 53 (after 49) → 54 (after 50+52) → 55 (after 49+50+52+54)

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
| 43. Karar Dili & Skor Açıklanabilirliği | v6.0 | `/stocks` + `/stocks/[symbol]` | 2/2 | ✅ Complete | 2026-05-13 |
| 44. Backtest & Sinyal Dashboard | v6.0 | `/backtest` (yeni sayfa) | 2/2 | ✅ Complete | 2026-05-13 |
| 45. Veri Tazeliği & Sistem Sağlığı | v6.0 | `/stocks` + `/stocks/[symbol]` + AI | 2/2 | ✅ Complete | 2026-05-13 |
| 46. Portföy Risk Yönetimi | v6.0 | `/portfolio` | 2/2 | ✅ Complete | 2026-05-14 |
| 47. İşlem Disiplini & Günlüğü | v6.0 | `/portfolio` + backend | 3/3 | ✅ Complete | 2026-05-14 |
| 48. Veri Kalitesi Temeli | v7.0 | `/stocks` + `/stocks/[symbol]` + backend | TBD | ⬜ Not started | — |
| 49. Veri Zenginleştirme | v7.0 | `/stocks/[symbol]` + `/intelligence` | TBD | ⬜ Not started | — |
| 50. Market Regime Engine | v7.0 | `/` + `/stocks/[symbol]` + backend | TBD | ⬜ Not started | — |
| 51. Sektör Bazlı Skorlama | v7.0 | `/stocks/[symbol]` + backend | TBD | ⬜ Not started | — |
| 52. Portföy Analizi | v7.0 | `/portfolio` + `/stocks/[symbol]` | TBD | ⬜ Not started | — |
| 53. Türkçe NLP & Sentiment | v7.0 | `/intelligence` + `/stocks/[symbol]` + backend | TBD | ⬜ Not started | — |
| 54. Backtest Kalitesi | v7.0 | `/backtest` + backend | TBD | ⬜ Not started | — |
| 55. UI — Hisse Detay & Ön-işlem Checklist | v7.0 | `/stocks/[symbol]` | TBD | ⬜ Not started | — |

## Kuzey Yıldızı

Stalize, BIST100 odaklı ama BIST'i etkileyen yerel ve küresel tüm önemli akışları izleyebilen, tamamen gerçek veriye dayalı bir analiz terminalidir. Amaç günlük trade terminali değil; özellikle 3-12 ay ufkunda daha güçlü hisse seçimi ve portföy yönetimi yaptıran bir karar sistemi kurmak.

**Temel ilkeler:**
1. Mock yok, simülasyon yok, sentetik haber yok.
2. KAP şirket verisinde birinci kaynak.
3. Kaynak önceliği ülkeye göre değil, BIST etkisine göre.
4. Dokunulan her fazda UI tutarsızlığı aynı turda düzeltilir.
5. Veri gelmiyorsa sistem boş döner; yanlış tahmin üretmez.
