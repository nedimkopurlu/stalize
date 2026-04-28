# Roadmap: Stalize Gerçek Veri Finansal Analiz Sistemi

## Milestones

- ✅ **v2.0 Gerçek Veri Çekirdeği** — Phases 01–16 (shipped 2026-04-27)
- ✅ **v3.0 Tüm Borsa + Kullanılabilir Platform** — Phases 17–21 (shipped 2026-04-28)
- 🔄 **v4.0 Audit Düzeltmeleri** — Phases 22–27 (aktif)

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

### v4.0 Audit Düzeltmeleri (Phases 22–27) — AKTİF

- [ ] **Phase 22: Async Infrastructure** — Event loop ve bağlantı havuzu sağlığı
- [ ] **Phase 23: Security Hardening** — Endpoint auth, CORS, hata sanitizasyonu
- [ ] **Phase 24: Data Reliability** — KAP sembol kapsamı, datetime doğruluğu, cache sınırları
- [ ] **Phase 25: Business Logic Correctness** — Skor tutarlılığı, screener validasyonu, volatilite
- [ ] **Phase 26: Frontend Quality** — Hata görünürlüğü, tip güvenliği, form validasyonu
- [ ] **Phase 27: Infrastructure Upgrade** — Python 3.12, health endpoint, structured logging

## Phase Details

### Phase 22: Async Infrastructure
**Goal**: Servis, yük altında event loop'u bloke etmeden ve bağlantı havuzunu sızdırmadan çalışıyor.
**Depends on**: Nothing (first v4.0 phase)
**Requirements**: ASYNC-01, ASYNC-02, ASYNC-03, ASYNC-04
**Success Criteria** (what must be TRUE):
  1. Yfinance retry sırasında diğer API request'leri yanıt vermeye devam ediyor; `time.sleep()` kodu artık yok.
  2. API route'larının hiçbirinde `AsyncSessionLocal()` doğrudan çağrısı yok; tüm DB erişimi `Depends(get_db)` üzerinden geçiyor.
  3. 14 scheduler job aynı anda tetiklenmiyor; ardışık başlatma ile thundering herd gözlemlenmiyor.
  4. Uygulama başlatıldığında bir `asyncio.create_task()` hatası oluşursa servis sessizce kırık başlamıyor; hata log'da görünüyor ve health durumuna yansıyor.
**Plans**: TBD

### Phase 23: Security Hardening
**Goal**: Tüm mutasyon endpoint'leri kimlik doğrulaması gerektiriyor ve API response'ları iç hata detaylarını sızdırmıyor.
**Depends on**: Phase 22
**Requirements**: SEC-01, SEC-02, SEC-03, SEC-04
**Success Criteria** (what must be TRUE):
  1. API key olmadan hiçbir POST veya DELETE endpoint'i başarılı dönmüyor; kimlik doğrulamasız istek HTTP 401/403 alıyor.
  2. CORS konfigürasyonu wildcard origin içermiyor; yalnızca izin verilen origin'ler kabul ediliyor.
  3. Bir endpoint hata fırlatırsa istemci `str(e)` değil generic bir hata mesajı görüyor; detaylı hata yalnızca server log'da görünüyor.
  4. Uygulama varsayılan olarak `DEBUG=False` ve SQL echo kapalı başlıyor; env var ile override edilebiliyor.
**Plans**: TBD

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
**Plans**: TBD

### Phase 25: Business Logic Correctness
**Goal**: Skor hesaplama tutarlı, screener geçersiz girdileri reddediyor ve portföy P&L eksik fiyatları işaretliyor.
**Depends on**: Phase 24
**Requirements**: LOGIC-01, LOGIC-02, LOGIC-03, LOGIC-04
**Success Criteria** (what must be TRUE):
  1. Aynı hisse için `calculate_overall_score()` ve `get_contextual_score_breakdown()` aynı ağırlıkları kullanıyor; API'nin öneri ve breakdown alanları çelişmiyor.
  2. Screener'a `pe_ratio_min > pe_ratio_max` gibi geçersiz aralık gönderildiğinde HTTP 400 dönüyor; boş sonuç listesi ile sessizce geçmek yerine hata açık.
  3. ATR volatilite bileşeni teknik skorda aktif; yüksek volatiliteli hisse ile düşük volatiliteli hisse aynı teknik puanı almıyor.
  4. Portföy P&L response'unda fiyat alınamayan pozisyonlar `partial: true` ile işaretlenmiş olarak dönüyor.
**Plans**: TBD

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
**Plans**: TBD

### Phase 27: Infrastructure Upgrade
**Goal**: Servis Python 3.12 üzerinde çalışıyor, sağlık durumu gerçek DB bağlantısını yansıtıyor ve log'lar makine tarafından parse edilebilir.
**Depends on**: Phase 22
**Requirements**: INFRA-01, INFRA-02, INFRA-03
**Success Criteria** (what must be TRUE):
  1. Backend Python 3.12 ile başarıyla başlıyor; tüm bağımlılıklar 3.12-compatible; 3.9'a özgü sözdizimi yok.
  2. `/health` endpoint'i DB'ye gerçek bağlantı testi yapıyor; DB düşükse endpoint başarısız (non-200) dönüyor.
  3. Uygulama log'ları emoji içermiyor ve structured format kullanıyor; kritik job hataları log'da aranabilir durumda.
**Plans**: TBD

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 22. Async Infrastructure | 0/? | Not started | - |
| 23. Security Hardening | 0/? | Not started | - |
| 24. Data Reliability | 0/? | Not started | - |
| 25. Business Logic Correctness | 0/? | Not started | - |
| 26. Frontend Quality | 0/? | Not started | - |
| 27. Infrastructure Upgrade | 0/? | Not started | - |

## Kuzey Yıldızı

Stalize, BIST100 odaklı ama BIST'i etkileyen yerel ve küresel tüm önemli akışları izleyebilen, tamamen gerçek veriye dayalı bir analiz terminalidir. Amaç günlük trade terminali değil; özellikle 3-12 ay ufkunda daha güçlü hisse seçimi ve portföy yönetimi yaptıran bir karar sistemi kurmak.

**Temel ilkeler:**
1. Mock yok, simülasyon yok, sentetik haber yok.
2. KAP şirket verisinde birinci kaynak.
3. Kaynak önceliği ülkeye göre değil, BIST etkisine göre.
4. Dokunulan her fazda UI tutarsızlığı aynı turda düzeltilir.
5. Veri gelmiyorsa sistem boş döner; yanlış tahmin üretmez.
